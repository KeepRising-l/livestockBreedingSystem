"""
回归测试（针对用户反馈的三处问题）：

1. 审核中心「一键通过」：新增 POST /review/batch-audit，一次审掉全部待审核记录，
   单条失败不影响其它条；员工（user_type=3）无权调用。
2. 物资统计「库存状态分布」改为「各物资库存量分布」：新增 name_dist（按物资名称聚合
   数量/单位/金额），原 status_dist 保留兼容。
3. 利润汇总「人工薪资总成本」只算已发放：待发放薪资不计入饲养总成本，
   单独在 labor_pending 返回。
"""
from tests.conftest import login, register_farm, TestingSessionLocal
from app.modules.finance.model import SalaryRecord


def _add_pen(client, h, code="A01", capacity=12):
    r = client.post("/api/v1/pen/add", json={
        "pen_code": code, "pen_type": "A", "capacity": capacity, "species": "牛",
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    return r.json()["data"]["id"]


def _add_animal(client, h, pen_id):
    r = client.post("/api/v1/animal/individual", json={
        "species": "牛", "breed": "黄牛", "gender": "母",
        "birth_date": "2026-01-01", "in_date": "2026-08-01",
        "source": "外购", "pen_id": pen_id,
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    return r.json()["data"]["ear_tag"]


# ============================================================
# 1. 审核中心一键通过
# ============================================================

def test_batch_audit_approves_all_pending(client):
    h = register_farm(client, "一键审核牛场", "batch_audit_owner")
    pen_id = _add_pen(client, h, "A01", capacity=10)
    tag = _add_animal(client, h, pen_id)

    # 造两类待审核：饲喂 + 防疫
    r = client.post("/api/v1/feeding/record/add", json={
        "pen_id": pen_id, "feed_date": "2026-09-01", "time_period": "早",
        "animal_count": 1, "feed_cost": 30,
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    r = client.post("/api/v1/health/vaccine/add", json={
        "ear_tag": tag, "species": "牛", "vaccine_date": "2026-09-02",
        "vaccine_type": "口蹄疫", "vaccine_name": "口蹄疫疫苗", "dosage": "1ml",
    }, headers=h)
    assert r.json()["code"] == 200, r.json()

    r = client.get("/api/v1/review/counts", headers=h)
    assert r.json()["data"]["total"] == 2, r.json()

    # 一键通过
    r = client.post("/api/v1/review/batch-audit", json={"audit_status": "通过"}, headers=h)
    assert r.json()["code"] == 200, r.json()
    assert r.json()["data"]["success"] == 2, r.json()
    assert r.json()["data"]["failed"] == 0, r.json()

    # 待审核清零，记录状态已变
    r = client.get("/api/v1/review/counts", headers=h)
    assert r.json()["data"]["total"] == 0, r.json()

    # 再点一次：没有待审核，明确提示而不是报错
    r = client.post("/api/v1/review/batch-audit", json={"audit_status": "通过"}, headers=h)
    assert r.json()["code"] == 200, r.json()
    assert r.json()["data"]["success"] == 0
    assert "没有待审核" in r.json()["msg"]


def test_batch_audit_can_limit_business_type(client):
    h = register_farm(client, "按类型一键审核牛场", "batch_type_owner")
    pen_id = _add_pen(client, h, "A01", capacity=10)
    tag = _add_animal(client, h, pen_id)

    client.post("/api/v1/feeding/record/add", json={
        "pen_id": pen_id, "feed_date": "2026-09-01", "time_period": "早",
        "animal_count": 1, "feed_cost": 30,
    }, headers=h)
    client.post("/api/v1/health/vaccine/add", json={
        "ear_tag": tag, "species": "牛", "vaccine_date": "2026-09-02",
        "vaccine_type": "口蹄疫", "vaccine_name": "口蹄疫疫苗", "dosage": "1ml",
    }, headers=h)

    # 只审防疫，饲喂仍待审核
    r = client.post("/api/v1/review/batch-audit",
                    json={"business_type": "vaccine", "audit_status": "通过"}, headers=h)
    assert r.json()["code"] == 200, r.json()
    assert r.json()["data"]["success"] == 1

    r = client.get("/api/v1/review/counts", headers=h)
    data = r.json()["data"]
    assert data["vaccine"] == 0
    assert data["feeding"] == 1
    assert data["total"] == 1


def test_batch_audit_rejects_employee(client):
    h = register_farm(client, "员工一键审核牛场", "batch_emp_owner")
    r = client.post("/api/v1/farm/employees", json={
        "username": "batch_feeder", "password": "123456", "real_name": "批量饲喂员",
        "phone": "13900000003", "post": "饲喂员",
    }, headers=h)
    assert r.json()["code"] == 200, r.json()

    emp = login(client, "batch_feeder", "123456")
    r = client.post("/api/v1/review/batch-audit", json={"audit_status": "通过"}, headers=emp)
    # 员工连 review 模块权限都没有 → 40303；即便有也不能审（40301）
    assert r.json()["code"] in (40301, 40303), r.json()


def test_batch_audit_invalid_status(client):
    h = register_farm(client, "非法状态审核牛场", "batch_bad_owner")
    r = client.post("/api/v1/review/batch-audit",
                    json={"audit_status": "随便"}, headers=h)
    assert r.json()["code"] == 40202, r.json()


# ============================================================
# 2. 物资统计：各物资库存量分布
# ============================================================

def test_material_stats_name_dist(client):
    h = register_farm(client, "物资分布牛场", "mat_dist_owner")

    # 两种物资，各建库存
    for name, qty, price, unit in (("玉米精料", 100, 3.5, "kg"), ("青霉素钠", 10, 20, "瓶")):
        r = client.post("/api/v1/inventory/purchase/add", json={
            "material_type": "饲料" if name == "玉米精料" else "兽药",
            "material_name": name, "batch_no": "B01",
            "quantity": qty, "unit": unit, "cost_price": price,
            "purchase_date": "2026-09-01",
        }, headers=h)
        pid = r.json()["data"]["id"]
        r = client.post(f"/api/v1/inventory/purchase/audit/{pid}",
                        json={"audit_status": "通过"}, headers=h)
        assert r.json()["code"] == 200, r.json()

    r = client.get("/api/v1/statistics/material", headers=h)
    assert r.json()["code"] == 200, r.json()
    data = r.json()["data"]

    assert "name_dist" in data
    rows = {row["name"]: row for row in data["name_dist"]}
    assert set(rows) == {"玉米精料", "青霉素钠"}
    assert rows["玉米精料"]["value"] == 100
    assert rows["玉米精料"]["unit"] == "kg"
    assert abs(rows["玉米精料"]["amount"] - 350) < 0.01
    assert rows["青霉素钠"]["value"] == 10
    assert abs(rows["青霉素钠"]["amount"] - 200) < 0.01
    # 按数量降序
    assert data["name_dist"][0]["name"] == "玉米精料"
    # 旧的 status_dist 仍然返回（兼容）
    assert "status_dist" in data


# ============================================================
# 3. 人工薪资只统计已发放
# ============================================================

def test_labor_cost_only_counts_paid_salary(client):
    h = register_farm(client, "薪资口径牛场", "salary_scope_owner")
    admin = login(client, "admin", "admin123")
    r = client.get("/api/v1/farm/list", headers=admin)
    farm_id = next(f["id"] for f in r.json()["data"] if f["farm_name"] == "薪资口径牛场")

    with TestingSessionLocal() as db:
        db.add(SalaryRecord(
            farm_id=farm_id, user_id=1, post="饲喂员", pay_month="2026-08",
            base_salary=3000, bonus=0, deduct=0, actual_pay=3000, status="已发放",
        ))
        db.add(SalaryRecord(
            farm_id=farm_id, user_id=1, post="兽医", pay_month="2026-08",
            base_salary=5000, bonus=0, deduct=0, actual_pay=5000, status="待发放",
        ))
        db.commit()

    r = client.get("/api/v1/finance/profit/summary", headers=h, params={
        "start_date": "2026-01-01", "end_date": "2026-12-31",
    })
    assert r.json()["code"] == 200, r.json()
    s = r.json()["data"]

    # 只有已发放的 3000 进成本，5000 待发放单列
    assert abs(s["labor_cost"] - 3000) < 0.01, s
    assert abs(s["labor_pending"] - 5000) < 0.01, s
    # 饲养总成本里不含待发放
    assert abs(s["breeding_cost"] - 3000) < 0.01, s


def test_labor_cost_moves_after_payment(client):
    """发放后成本立即增加，待发放归零"""
    h = register_farm(client, "发放即计入牛场", "salary_pay_owner")
    admin = login(client, "admin", "admin123")
    r = client.get("/api/v1/farm/list", headers=admin)
    farm_id = next(f["id"] for f in r.json()["data"] if f["farm_name"] == "发放即计入牛场")

    with TestingSessionLocal() as db:
        rec = SalaryRecord(
            farm_id=farm_id, user_id=1, post="饲喂员", pay_month="2026-09",
            base_salary=4000, bonus=0, deduct=0, actual_pay=4000, status="待发放",
        )
        db.add(rec)
        db.commit()
        rec_id = rec.id

    r = client.get("/api/v1/finance/profit/summary", headers=h)
    s = r.json()["data"]
    assert abs(s["labor_cost"] - 0) < 0.01
    assert abs(s["labor_pending"] - 4000) < 0.01

    r = client.post(f"/api/v1/finance/salary/pay/{rec_id}", headers=h)
    assert r.json()["code"] == 200, r.json()

    r = client.get("/api/v1/finance/profit/summary", headers=h)
    s = r.json()["data"]
    assert abs(s["labor_cost"] - 4000) < 0.01
    assert abs(s["labor_pending"] - 0) < 0.01
