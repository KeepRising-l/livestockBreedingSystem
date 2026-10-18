"""
优化需求单回归测试：

1. 销售财务：出栏后档案联动删除（转入历史记录）、圈舍自动腾出、销售明细快照保留
2. 销售财务：利润汇总新口径（进货支出 + 物资消耗 + 人工薪资 + 其他成本 = 饲养总成本）
3. 饲喂管理：批量提交（一次按多个圈舍生成多条，同圈舍同日同时段去重跳过）
4. 销售订单：生长阶段按出生日期实时计算（与档案管理页一致，不读陈旧存储值）
"""
from datetime import date, timedelta

from tests.conftest import login, register_farm, TestingSessionLocal
from app.modules.finance.model import SalaryRecord


def _add_pen(client, h, code="A01", capacity=12):
    r = client.post("/api/v1/pen/add", json={
        "pen_code": code, "pen_type": "A", "capacity": capacity, "species": "牛",
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    return r.json()["data"]["id"]


def _add_animal(client, h, pen_id, birth_date="2026-01-01", gender="母"):
    r = client.post("/api/v1/animal/individual", json={
        "species": "牛", "breed": "黄牛", "gender": gender,
        "birth_date": birth_date, "in_date": "2026-08-01",
        "source": "外购", "pen_id": pen_id,
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    return r.json()["data"]["ear_tag"]


# ============================================================
# 1. 出栏销售后档案联动删除
# ============================================================

def test_sale_out_removes_archive_to_history(client):
    h = register_farm(client, "出栏删档牛场", "sale_del_owner")
    pen_id = _add_pen(client, h, "A01", capacity=5)
    tags = [_add_animal(client, h, pen_id) for _ in range(2)]

    r = client.post("/api/v1/finance/sale/out", json={
        "customer": "张老板", "unit_price": 20.0, "order_date": "2026-09-01",
        "items": [{"ear_tag": tags[0], "weight": 300}],
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    order_id = r.json()["data"]["id"]

    # 档案列表里只剩没卖的那一头（卖掉的已逻辑删除）
    r = client.get("/api/v1/animal/list", headers=h)
    assert r.json()["data"]["total"] == 1
    assert r.json()["data"]["list"][0]["ear_tag"] == tags[1]

    # 历史记录里有卖掉的这一头，状态是已出栏
    r = client.get("/api/v1/animal/history/list", headers=h)
    assert r.json()["data"]["total"] == 1
    hist = r.json()["data"]["list"][0]
    assert hist["ear_tag"] == tags[0]
    assert hist["status"] == "已出栏"
    assert hist["out_date"] == "2026-09-01"

    # 圈舍存栏只减了 1（不是 0 也不是 -2）
    r = client.get(f"/api/v1/pen/{pen_id}", headers=h)
    assert r.json()["data"]["current_count"] == 1

    # 销售明细快照保留，仍能追溯耳标与成本
    r = client.get(f"/api/v1/finance/sale/{order_id}", headers=h)
    details = r.json()["data"]["details"]
    assert len(details) == 1
    assert details[0]["ear_tag"] == tags[0]

    # 已删除的档案不能再出栏
    r = client.post("/api/v1/finance/sale/out", json={
        "customer": "张老板", "unit_price": 20.0,
        "items": [{"ear_tag": tags[0], "weight": 300}],
    }, headers=h)
    assert r.json()["code"] == 40502


# ============================================================
# 2. 利润汇总口径
# ============================================================

def test_profit_summary_uses_purchase_consume_labor_other(client):
    h = register_farm(client, "利润核算牛场", "profit_owner")
    admin = login(client, "admin", "admin123")
    r = client.get("/api/v1/farm/list", headers=admin)
    farm_id = next(f["id"] for f in r.json()["data"] if f["farm_name"] == "利润核算牛场")

    pen_id = _add_pen(client, h, "A01", capacity=10)
    tag = _add_animal(client, h, pen_id)

    # 进货：100 kg × 3.2 元 = 320（审核通过才计入）
    r = client.post("/api/v1/inventory/purchase/add", json={
        "material_type": "饲料", "material_name": "玉米精料", "batch_no": "B001",
        "quantity": 100, "unit": "kg", "cost_price": 3.2, "purchase_date": "2026-08-10",
    }, headers=h)
    purchase_id = r.json()["data"]["id"]
    r = client.post(f"/api/v1/inventory/purchase/audit/{purchase_id}",
                    json={"audit_status": "通过"}, headers=h)
    stock_id = r.json()["data"]["stock_id"]

    # 领用：30 kg × 3.2 元 = 96
    r = client.post("/api/v1/inventory/consume/add", json={
        "stock_id": stock_id, "quantity": 30, "unit": "kg",
        "consume_date": "2026-08-11", "related_module": "饲喂",
    }, headers=h)
    consume_id = r.json()["data"]["id"]
    r = client.post(f"/api/v1/inventory/consume/audit/{consume_id}",
                    json={"audit_status": "通过"}, headers=h)
    assert r.json()["code"] == 200, r.json()

    # 其他成本：水电 200
    r = client.post("/api/v1/finance/expense/add", json={
        "expense_type": "水电", "amount": 200, "expense_date": "2026-08-12",
    }, headers=h)
    assert r.json()["code"] == 200, r.json()

    # 人工薪资：直接落一条薪资记录（接口按月生成需要先有员工）
    with TestingSessionLocal() as db:
        db.add(SalaryRecord(
            farm_id=farm_id, user_id=1, post="饲喂员", pay_month="2026-08",
            base_salary=3000, bonus=0, deduct=0, actual_pay=3000, status="已发放",
        ))
        db.commit()

    # 销售：300 kg × 20 = 6000
    r = client.post("/api/v1/finance/sale/out", json={
        "customer": "李老板", "unit_price": 20.0, "order_date": "2026-09-01",
        "items": [{"ear_tag": tag, "weight": 300}],
    }, headers=h)
    assert r.json()["code"] == 200, r.json()

    r = client.get("/api/v1/finance/profit/summary", headers=h, params={
        "start_date": "2026-01-01", "end_date": "2026-12-31",
    })
    assert r.json()["code"] == 200, r.json()
    s = r.json()["data"]

    assert s["order_count"] == 1
    assert s["animal_count"] == 1
    assert abs(s["total_amount"] - 6000) < 0.01
    assert abs(s["purchase_cost"] - 320) < 0.01
    assert abs(s["consume_cost"] - 96) < 0.01
    assert abs(s["labor_cost"] - 3000) < 0.01
    assert abs(s["other_cost"] - 200) < 0.01
    # 饲养总成本 = 320 + 96 + 3000 + 200
    assert abs(s["breeding_cost"] - 3616) < 0.01
    # 盈利金额 = 销售金额 - 饲养总成本
    assert abs(s["profit"] - (6000 - 3616)) < 0.01
    assert abs(s["profit_rate"] - round((6000 - 3616) / 6000 * 100, 2)) < 0.01
    # 兼容字段
    assert abs(s["total_cost"] - s["breeding_cost"]) < 0.01
    assert abs(s["net_profit"] - s["profit"]) < 0.01
    # 销售金额绝不能混进成本里
    assert s["breeding_cost"] < s["total_amount"]

    # 查一段没有业务发生的时间，成本应为 0（不会被销售额污染）
    r = client.get("/api/v1/finance/profit/summary", headers=h, params={
        "start_date": "2025-01-01", "end_date": "2025-12-31",
    })
    s0 = r.json()["data"]
    assert s0["total_amount"] == 0
    assert s0["purchase_cost"] == 0
    assert s0["breeding_cost"] == 0
    assert s0["profit"] == 0


# ============================================================
# 3. 饲喂记录批量提交
# ============================================================

def test_feeding_batch_add_multiple_pens(client):
    h = register_farm(client, "批量饲喂牛场", "feeding_batch_owner")
    pen_a = _add_pen(client, h, "A01", capacity=10)
    pen_b = _add_pen(client, h, "A02", capacity=10)
    for _ in range(2):
        _add_animal(client, h, pen_a)
    _add_animal(client, h, pen_b)

    r = client.post("/api/v1/feeding/plan/add", json={
        "species": "cattle", "plan_name": "育肥方案", "applicable_stage": "育肥期",
        "feed_times_per_day": 2, "concentrate_weight": 2.5, "silage_weight": 5.0,
        "hay_weight": 1.0, "concentrate_price": 3200, "silage_price": 600, "hay_price": 1200,
    }, headers=h)
    plan_id = r.json()["data"]["id"]

    payload = {
        "feed_date": "2026-08-10", "time_period": "早", "plan_id": plan_id,
        "status": "已投喂",
        "items": [
            {"pen_id": pen_a, "animal_count": 2, "actual_concentrate": 5.0,
             "actual_silage": 10.0, "actual_hay": 2.0},
            {"pen_id": pen_b, "animal_count": 1, "actual_concentrate": 2.5,
             "actual_silage": 5.0, "actual_hay": 1.0},
        ],
    }
    r = client.post("/api/v1/feeding/record/batch-add", json=payload, headers=h)
    assert r.json()["code"] == 200, r.json()
    assert r.json()["data"]["created"] == 2
    assert r.json()["data"]["skipped"] == []

    # 一次提交生成 2 条记录，计划重量/成本自动带出
    r = client.get("/api/v1/feeding/record/list", headers=h, params={"pageSize": 50})
    items = r.json()["data"]["list"]
    assert r.json()["data"]["total"] == 2
    by_pen = {x["pen_id"]: x for x in items}
    assert by_pen[pen_a]["animal_count"] == 2
    assert float(by_pen[pen_a]["plan_concentrate"]) == 2.5
    assert float(by_pen[pen_a]["feed_cost"]) == 24.4  # (5*3200+10*600+2*1200)/1000
    assert float(by_pen[pen_b]["feed_cost"]) == 12.2
    assert all(x["audit_status"] == "待审核" for x in items)

    # 同一天同一时段重复提交 → 全部跳过，不产生重复记录
    r = client.post("/api/v1/feeding/record/batch-add", json=payload, headers=h)
    assert r.json()["code"] == 200, r.json()
    assert r.json()["data"]["created"] == 0
    assert len(r.json()["data"]["skipped"]) == 2
    assert all("已有饲喂记录" in s["reason"] for s in r.json()["data"]["skipped"])
    r = client.get("/api/v1/feeding/record/list", headers=h, params={"pageSize": 50})
    assert r.json()["data"]["total"] == 2

    # 换成晚时段可以正常提交
    payload2 = dict(payload)
    payload2["time_period"] = "晚"
    r = client.post("/api/v1/feeding/record/batch-add", json=payload2, headers=h)
    assert r.json()["data"]["created"] == 2


# ============================================================
# 4. 销售订单生长阶段实时计算
# ============================================================

def test_sale_candidates_growth_stage_is_live(client):
    h = register_farm(client, "生长阶段牛场", "stage_owner")
    pen_id = _add_pen(client, h, "A01", capacity=10)

    # 出生日期 = 373 天前；入栏时按当时的日龄写了"生长期"，之后没有刷新（模拟陈旧数据）
    birth = date.today() - timedelta(days=373)
    tag = _add_animal(client, h, pen_id, birth_date=birth.isoformat())
    from app.modules.animal.model import Animal
    with TestingSessionLocal() as db:
        a = db.query(Animal).filter(Animal.ear_tag == tag, Animal.deleted == False).first()
        a.growth_stage = "生长期"
        db.commit()

    # 档案管理页实时算 → 育肥期
    r = client.get("/api/v1/animal/list", headers=h)
    archive_stage = r.json()["data"]["list"][0]["growth_stage"]
    assert archive_stage == "育肥期"

    # 销售订单候选也必须一致（此前直接返回陈旧的"生长期"）
    r = client.get("/api/v1/finance/sale/candidates", headers=h)
    assert r.json()["code"] == 200, r.json()
    cand = next(c for c in r.json()["data"] if c["ear_tag"] == tag)
    assert cand["growth_stage"] == archive_stage == "育肥期"
    assert cand["age_days"] == 373


# ============================================================
# 5. 圈舍批量添加
# ============================================================

def test_pen_batch_add(client):
    h = register_farm(client, "批量圈舍牛场", "pen_batch_owner")

    r = client.post("/api/v1/pen/batch-add", json={
        "species": "牛", "pen_type": "A", "capacity": 10,
        "prefix": "A", "start_no": 1, "count": 3,
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    assert r.json()["data"]["created"] == 3
    assert r.json()["data"]["created_codes"] == ["A01", "A02", "A03"]
    assert r.json()["data"]["skipped"] == []

    # 已存在的编号 + 本次内部重复 → 跳过并给出原因，不影响其它编号
    r = client.post("/api/v1/pen/batch-add", json={
        "species": "牛", "pen_type": "A", "capacity": 10,
        "codes": ["A01", "A04", "A04", "A05"],
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    assert r.json()["data"]["created"] == 2
    assert r.json()["data"]["created_codes"] == ["A04", "A05"]
    assert len(r.json()["data"]["skipped"]) == 2

    # 数量超上限 → 业务错误
    r = client.post("/api/v1/pen/batch-add", json={
        "species": "牛", "pen_type": "A", "capacity": 10,
        "prefix": "B", "start_no": 1, "count": 51,
    }, headers=h)
    assert r.json()["code"] == 40023

    # 员工无权
    r = client.get("/api/v1/pen/list", headers=h)
    assert r.json()["data"]["total"] == 5


# ============================================================
# 6. 批量防疫：按圈舍取在栏耳标
# ============================================================

def test_vaccine_pen_animals_grouped_by_pen(client):
    h = register_farm(client, "批量防疫牛场", "vaccine_pen_owner")
    pen_a = _add_pen(client, h, "A01", capacity=10)
    pen_b = _add_pen(client, h, "A02", capacity=10)
    tag_a = _add_animal(client, h, pen_a)
    tag_b = _add_animal(client, h, pen_b)

    r = client.get("/api/v1/health/vaccine/pen-animals", headers=h, params={"species": "牛"})
    assert r.json()["code"] == 200, r.json()
    groups = r.json()["data"]
    assert {g["pen_code"] for g in groups} == {"A01", "A02"}
    assert [g["pen_code"] for g in groups] == ["A01", "A02"]  # 圈舍编号升序
    by_pen = {g["pen_code"]: [a["ear_tag"] for a in g["animals"]] for g in groups}
    assert by_pen["A01"] == [tag_a]
    assert by_pen["A02"] == [tag_b]

    # 已出栏的不再出现在在栏列表里
    tag_c = _add_animal(client, h, pen_a)
    client.post("/api/v1/finance/sale/out", json={
        "customer": "王老板", "unit_price": 20.0, "order_date": "2026-09-01",
        "items": [{"ear_tag": tag_c, "weight": 300}],
    }, headers=h)
    r = client.get("/api/v1/health/vaccine/pen-animals", headers=h)
    tags = [a["ear_tag"] for g in r.json()["data"] for a in g["animals"]]
    assert tag_c not in tags
    assert set(tags) == {tag_a, tag_b}


# ============================================================
# 7. 兽医角色不再包含「物资库存」
# ============================================================

def test_vet_role_perms_without_inventory(client):
    import json
    from app.main import _ensure_vet_role_perms
    from app.modules.system.model import SysRole
    from app.modules.system.service import ROLE_PERMS

    assert "inventory" not in ROLE_PERMS["vet"]

    # 模拟老库：vet 角色的 perms 里残留 inventory
    with TestingSessionLocal() as db:
        db.add(SysRole(
            role_name="兽医", role_key="vet", sort=4, status=1,
            perms=json.dumps(["dashboard", "pen", "animal", "health", "inventory"]),
        ))
        db.commit()
        _ensure_vet_role_perms(db)
        role = db.query(SysRole).filter(SysRole.role_key == "vet").first()
        assert json.loads(role.perms) == ["dashboard", "pen", "animal", "health"]
        # 幂等：再调一次不报错、结果不变
        _ensure_vet_role_perms(db)
        db.refresh(role)
        assert json.loads(role.perms) == ["dashboard", "pen", "animal", "health"]
