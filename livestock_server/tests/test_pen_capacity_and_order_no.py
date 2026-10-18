"""
回归测试（端到端验证中发现的问题）：

1. 销售订单号「场内唯一」：两个养殖场同一天各自出第一单，编号都是 SO{日期}001，
   老库上 order_no 带全局 UNIQUE 索引 → B 场出栏直接 IntegrityError 500。
   编号口径本来就是按 farm_id 统计的，因此唯一性只能在场内保证。
2. 档案状态改成「已出栏 / 死亡」时同步释放圈舍存栏：此前只改状态不扣 current_count，
   圈舍存栏虚高会让自动分圈找不到空位、容量校验误报「已满」。
3. 员工被删除后旧 token 立即失效：此前 get_current_user 只校验 status，
   删掉的员工还能拿旧 token 一直操作本场数据。
"""
from datetime import date

from tests.conftest import login, register_farm
from app.modules.animal.model import Animal
from app.modules.finance.model import SaleOrder
from tests.conftest import TestingSessionLocal


def _add_pen(client, h, code="A01", capacity=12, pen_type="A", species="牛"):
    r = client.post("/api/v1/pen/add", json={
        "pen_code": code, "pen_type": pen_type, "capacity": capacity, "species": species,
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
# 1. 订单号按养殖场独立编号（不再要求全局唯一）
# ============================================================

def test_sale_order_no_is_unique_per_farm_only(client):
    """两个场同一天出栏，编号相同也不该报错，且各自能查到自己的订单"""
    # 模型层：order_no 不能是全局唯一列（唯一性只在 farm_id 范围内成立）
    assert not SaleOrder.__table__.c.order_no.unique

    order_date = "2026-09-01"
    nos = []
    for farm_no in (1, 2):
        h = register_farm(client, f"同日编号牛场{farm_no}", f"same_day_owner_{farm_no}")
        pen_id = _add_pen(client, h, "A01", capacity=5)
        tag = _add_animal(client, h, pen_id)
        r = client.post("/api/v1/finance/sale/out", json={
            "customer": "同日客户", "unit_price": 20.0, "order_date": order_date,
            "items": [{"ear_tag": tag, "weight": 300}],
        }, headers=h)
        assert r.json()["code"] == 200, r.json()
        nos.append(r.json()["data"]["order_no"])

        # 各自的订单列表里只有自己那一单
        r = client.get("/api/v1/finance/sale/list", headers=h)
        assert r.json()["data"]["total"] == 1
        assert r.json()["data"]["list"][0]["order_no"] == nos[-1]

    assert nos == [f"SO20260901001", f"SO20260901001"], nos


def test_sale_order_no_skips_existing_then_increments(client):
    """同场内同日第二单递增；中间有跳号/删号也不会撞上已有编号"""
    h = register_farm(client, "同场连续编号牛场", "seq_owner")
    pen_id = _add_pen(client, h, "A01", capacity=5)
    tags = [_add_animal(client, h, pen_id) for _ in range(3)]

    with TestingSessionLocal() as db:
        db.add(SaleOrder(
            farm_id=1, order_no="SO20260901999", customer="占位",
            animal_count=0, total_weight=0, unit_price=0, total_amount=0,
            order_date=date(2026, 9, 1), settle_status="未结算", species="牛",
        ))
        db.commit()

    r = client.post("/api/v1/finance/sale/out", json={
        "customer": "甲", "unit_price": 20.0, "order_date": "2026-09-01",
        "items": [{"ear_tag": tags[0], "weight": 300}],
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    assert r.json()["data"]["order_no"] == "SO20260901001"

    r = client.post("/api/v1/finance/sale/out", json={
        "customer": "乙", "unit_price": 20.0, "order_date": "2026-09-01",
        "items": [{"ear_tag": tags[1], "weight": 300}],
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    assert r.json()["data"]["order_no"] == "SO20260901002"


# ============================================================
# 2. 档案状态改成「已出栏 / 死亡」时释放圈舍存栏
# ============================================================

def test_animal_status_change_to_sold_releases_pen_capacity(client):
    h = register_farm(client, "状态同步牛场", "status_sync_owner")
    pen_id = _add_pen(client, h, "A01", capacity=2)
    tag = _add_animal(client, h, pen_id)

    r = client.get(f"/api/v1/pen/{pen_id}", headers=h)
    assert r.json()["data"]["current_count"] == 1

    # 档案编辑里把状态改成「已出栏」→ 圈舍存栏应为 0
    animal = client.get("/api/v1/animal/list", headers=h).json()["data"]["list"][0]
    r = client.put(f"/api/v1/animal/update/{animal['id']}", json={"status": "已出栏"}, headers=h)
    assert r.json()["code"] == 200, r.json()
    assert client.get(f"/api/v1/pen/{pen_id}", headers=h).json()["data"]["current_count"] == 0

    # 改回「在栏」→ 存栏回到 1（容量允许）
    r = client.put(f"/api/v1/animal/update/{animal['id']}", json={"status": "在栏"}, headers=h)
    assert r.json()["code"] == 200, r.json()
    assert client.get(f"/api/v1/pen/{pen_id}", headers=h).json()["data"]["current_count"] == 1

    # 「死亡」同样释放存栏；重复改不回涨（幂等）
    r = client.put(f"/api/v1/animal/update/{animal['id']}", json={"status": "死亡"}, headers=h)
    assert r.json()["code"] == 200, r.json()
    r = client.put(f"/api/v1/animal/update/{animal['id']}", json={"status": "死亡"}, headers=h)
    assert r.json()["code"] == 200, r.json()
    assert client.get(f"/api/v1/pen/{pen_id}", headers=h).json()["data"]["current_count"] == 0


def test_animal_status_change_keeps_count_when_status_unchanged(client):
    """只是改品种等普通字段，不能动圈舍存栏"""
    h = register_farm(client, "普通编辑牛场", "plain_edit_owner")
    pen_id = _add_pen(client, h, "A01", capacity=5)
    _add_animal(client, h, pen_id)
    animal = client.get("/api/v1/animal/list", headers=h).json()["data"]["list"][0]

    r = client.put(f"/api/v1/animal/update/{animal['id']}", json={"breed": "夏洛莱"}, headers=h)
    assert r.json()["code"] == 200, r.json()
    assert client.get(f"/api/v1/pen/{pen_id}", headers=h).json()["data"]["current_count"] == 1

    # 状态传成同一个值也不该扣减
    r = client.put(f"/api/v1/animal/update/{animal['id']}", json={"status": "在栏"}, headers=h)
    assert r.json()["code"] == 200, r.json()
    assert client.get(f"/api/v1/pen/{pen_id}", headers=h).json()["data"]["current_count"] == 1


def test_sold_animal_sale_out_decrements_pen_once(client):
    """出栏销售：圈舍只减 1 次（出栏把状态改「已出栏」后仍必须腾位）"""
    h = register_farm(client, "出栏腾位牛场", "sale_pen_owner")
    pen_id = _add_pen(client, h, "A01", capacity=5)
    tags = [_add_animal(client, h, pen_id) for _ in range(3)]

    r = client.post("/api/v1/finance/sale/out", json={
        "customer": "腾位客户", "unit_price": 20.0, "order_date": "2026-09-01",
        "items": [{"ear_tag": tags[0], "weight": 300}],
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    assert client.get(f"/api/v1/pen/{pen_id}", headers=h).json()["data"]["current_count"] == 2

    # 历史档案恢复后回到在栏并重新占位
    hist = client.get("/api/v1/animal/history/list", headers=h).json()["data"]["list"][0]
    r = client.post(f"/api/v1/animal/history/restore/{hist['id']}", headers=h)
    assert r.json()["code"] == 200, r.json()
    assert client.get(f"/api/v1/pen/{pen_id}", headers=h).json()["data"]["current_count"] == 3
    restored = client.get("/api/v1/animal/list", headers=h, params={"ear_tag": tags[0]}).json()
    assert restored["data"]["total"] == 1
    assert restored["data"]["list"][0]["status"] == "在栏"
    assert restored["data"]["list"][0]["out_date"] is None


# ============================================================
# 3. 删除员工后旧 token 立即失效
# ============================================================

def test_deleted_employee_token_rejected(client):
    h = register_farm(client, "删员工牛场", "del_emp_owner")

    r = client.post("/api/v1/farm/employees", json={
        "username": "temp_feeder", "password": "123456", "real_name": "临时饲喂员",
        "phone": "13900000002", "post": "饲喂员",
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    emp_id = r.json()["data"]["user_id"]

    emp_h = login(client, "temp_feeder", "123456")
    # 用「只要登录即可」的接口验证 token 有效（测试库不跑 init_rbac_data，没有角色数据）
    assert client.get("/api/v1/auth/permissions", headers=emp_h).json()["code"] == 200

    # 删掉员工后，旧 token 立刻不可用
    r = client.delete(f"/api/v1/farm/employees/{emp_id}", headers=h)
    assert r.json()["code"] == 200, r.json()
    body = client.get("/api/v1/auth/permissions", headers=emp_h).json()
    assert body["code"] == 401, body
    assert "删除" in body["msg"]
    # 重新登录也进不来
    r = client.post("/api/v1/auth/login", json={"username": "temp_feeder", "password": "123456"})
    assert r.json()["code"] != 200


def test_animal_update_occupying_status_respects_capacity(client):
    """把「已出栏」档案改回在栏时，圈舍满员要拦下（不能凭空超容）"""
    h = register_farm(client, "回栏容量牛场", "restore_cap_owner")
    pen_id = _add_pen(client, h, "A01", capacity=2)
    tags = [_add_animal(client, h, pen_id) for _ in range(2)]
    animal = client.get("/api/v1/animal/list", headers=h,
                        params={"ear_tag": tags[0]}).json()["data"]["list"][0]

    # 先标记已出栏（存栏 2 -> 1），再补一头占满（1 -> 2）
    r = client.put(f"/api/v1/animal/update/{animal['id']}", json={"status": "已出栏"}, headers=h)
    assert r.json()["code"] == 200, r.json()
    assert client.get(f"/api/v1/pen/{pen_id}", headers=h).json()["data"]["current_count"] == 1
    with TestingSessionLocal() as db:
        a = db.query(Animal).filter(Animal.ear_tag == tags[1], Animal.deleted == False).first()
        from app.modules.pen.model import Pen
        db.query(Pen).filter(Pen.id == pen_id).update({Pen.current_count: 2})
        db.commit()

    r = client.put(f"/api/v1/animal/update/{animal['id']}", json={"status": "在栏"}, headers=h)
    assert r.json()["code"] == 40030, r.json()
    assert client.get(f"/api/v1/pen/{pen_id}", headers=h).json()["data"]["current_count"] == 2
