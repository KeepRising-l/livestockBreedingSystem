"""
端到端冒烟测试：注册 → 登录 → 圈舍 → 入栏 → 鈐喂 → 审核 → 库存 → 出栏销售。

对应旧 quick_test.py 的"快速验证整个请求链路"职责，改为可重复、可断言的
pytest 用例（quick_test.py 现在只是本文件的薄包装）。
"""
from tests.conftest import register_farm


def test_end_to_end_smoke(client):
    # 1. 健康检查
    assert client.get("/health").json()["status"] == "up"

    # 2. 注册场主 + 登录
    h = register_farm(client, "冒烟牛场", "smoke_owner")

    # 3. 圈舍
    r = client.post("/api/v1/pen/add", json={"pen_code": "A01", "pen_type": "A", "capacity": 12}, headers=h)
    assert r.json()["code"] == 200, r.json()
    pen_id = r.json()["data"]["id"]

    # 4. 个体入栏 ×2
    ear_tags = []
    for _ in range(2):
        r = client.post("/api/v1/animal/individual", json={
            "species": "牛", "breed": "黄牛", "gender": "母",
            "birth_date": "2026-01-01", "in_date": "2026-08-01",
            "source": "外购", "pen_id": pen_id,
        }, headers=h)
        assert r.json()["code"] == 200, r.json()
        ear_tags.append(r.json()["data"]["ear_tag"])

    # 5. 饲喂方案 + 记录 + 审核
    r = client.post("/api/v1/feeding/plan/add", json={
        "species": "cattle", "plan_name": "育肥牛方案", "applicable_stage": "育肥期",
        "feed_times_per_day": 2, "concentrate_weight": 2.5, "silage_weight": 5.0,
        "hay_weight": 1.0, "concentrate_price": 3200, "silage_price": 600, "hay_price": 1200,
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    plan_id = r.json()["data"]["id"]

    r = client.post("/api/v1/feeding/record/add", json={
        "feed_date": "2026-08-10", "time_period": "早", "pen_id": pen_id, "plan_id": plan_id,
        "actual_concentrate": 5.0, "actual_silage": 10.0, "actual_hay": 2.0,
        "animal_count": 2, "status": "已投喂",
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    rec_id = r.json()["data"]["id"]
    assert r.json()["data"]["audit_status"] == "待审核"

    r = client.post(f"/api/v1/feeding/record/audit/{rec_id}", json={"audit_status": "通过"}, headers=h)
    assert r.json()["code"] == 200, r.json()
    assert r.json()["data"]["status"] == "已投喂"

    # 6. 库存：进货审核入库 → 领用审核扣减
    r = client.post("/api/v1/inventory/purchase/add", json={
        "material_type": "饲料", "material_name": "玉米精料",
        "batch_no": "B001", "quantity": 100, "unit": "kg", "cost_price": 3.2,
        "purchase_date": "2026-08-10",
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    purchase_id = r.json()["data"]["id"]

    r = client.post(f"/api/v1/inventory/purchase/audit/{purchase_id}", json={"audit_status": "通过"}, headers=h)
    assert r.json()["code"] == 200, r.json()
    stock_id = r.json()["data"]["stock_id"]

    r = client.get(f"/api/v1/inventory/stock/{stock_id}", headers=h)
    assert float(r.json()["data"]["quantity"]) == 100.0

    r = client.post("/api/v1/inventory/consume/add", json={
        "stock_id": stock_id, "quantity": 30, "unit": "kg",
        "consume_date": "2026-08-11", "related_module": "饲喂",
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    consume_id = r.json()["data"]["id"]

    r = client.post(f"/api/v1/inventory/consume/audit/{consume_id}", json={"audit_status": "通过"}, headers=h)
    assert r.json()["code"] == 200, r.json()
    r = client.get(f"/api/v1/inventory/stock/{stock_id}", headers=h)
    assert float(r.json()["data"]["quantity"]) == 70.0

    # 7. 出栏销售：成本按当条饲喂记录头数快照均分
    r = client.post("/api/v1/finance/sale/out", json={
        "customer": "张老板", "unit_price": 20.0,
        "items": [
            {"ear_tag": ear_tags[0], "weight": 300},
            {"ear_tag": ear_tags[1], "weight": 310},
        ],
        "order_date": "2026-09-01",
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    order_id = r.json()["data"]["id"]

    r = client.get(f"/api/v1/finance/sale/{order_id}", headers=h)
    assert r.json()["code"] == 200, r.json()
    details = r.json()["data"]["details"]
    assert len(details) == 2
    for d in details:
        # 饲喂成本 = (5*3200 + 10*600 + 2*1200)/1000 = 24.4 元/条，2 头均分 → 12.2
        assert abs(float(d["feed_cost"]) - 12.2) < 0.01, d
        parts = (float(d["feed_cost"]) + float(d["medicine_cost"])
                 + float(d["labor_cost"]) + float(d["consumable_cost"]))
        assert round(parts, 2) == float(d["total_cost"])
        assert round(float(d["sale_amount"]) - float(d["total_cost"]), 2) == float(d["profit"])

    # 8. 出栏后档案联动删除：转入历史记录，档案列表里不再出现（圈舍自动腾出）
    r = client.get("/api/v1/animal/list?status=已出栏", headers=h)
    assert r.json()["data"]["total"] == 0
    r = client.get("/api/v1/animal/history/list", headers=h)
    assert r.json()["data"]["total"] == 2
    assert {x["status"] for x in r.json()["data"]["list"]} == {"已出栏"}
    # 圈舍存栏回到 0
    r = client.get(f"/api/v1/pen/{pen_id}", headers=h)
    assert r.json()["data"]["current_count"] == 0

    # 9. 超管无 X-Farm-Id 访问业务接口：明确报错（不回退首个农场）
    from tests.conftest import login
    admin = login(client, "admin", "admin123")
    r = client.get("/api/v1/animal/list", headers=admin)
    assert r.json()["code"] == 40302, r.json()
