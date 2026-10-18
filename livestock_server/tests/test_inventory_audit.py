"""
P1-B 验收：库存审核与库存变更的原子性 / 一致性（顺序语义）。

说明：
- 本文件用 SQLite 验证"单据只审一次 / 库存不扣成负数 / 事务回滚"的顺序语义；
- 生产数据库（MySQL/InnoDB）下的真并发行为由 tests/test_concurrency_mysql.py
  覆盖（需设置 TEST_MYSQL_URL 后运行）。
"""
from tests.conftest import register_farm


def _setup_inventory(client, stock_qty=100):
    """建场 + 建库存物资（玉米精料 stock_qty kg），返回 (headers, stock_id)"""
    h = register_farm(client, "测试牛场", "owner1")
    r = client.post("/api/v1/inventory/stock/add", json={
        "material_type": "饲料",
        "material_name": "玉米精料",
        "specification": "50kg/袋",
        "quantity": stock_qty,
        "unit": "kg",
        "warning_threshold": 10,
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    return h, r.json()["data"]["id"]


def _add_purchase(client, h, qty, price, name="玉米精料"):
    r = client.post("/api/v1/inventory/purchase/add", json={
        "material_type": "饲料",
        "material_name": name,
        "batch_no": "B001",
        "quantity": qty,
        "unit": "kg",
        "cost_price": price,
        "purchase_date": "2026-08-10",
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    return r.json()["data"]["id"]


def _add_consume(client, h, stock_id, qty):
    r = client.post("/api/v1/inventory/consume/add", json={
        "stock_id": stock_id,
        "quantity": qty,
        "unit": "kg",
        "consume_date": "2026-08-10",
    }, headers=h)
    assert r.json()["code"] == 200, r.json()
    return r.json()["data"]["id"]


def _audit(client, h, path, rid, status="通过"):
    return client.post(f"/api/v1/inventory/{path}/audit/{rid}",
                       json={"audit_status": status}, headers=h)


def _stock_qty(client, h, stock_id):
    r = client.get(f"/api/v1/inventory/stock/{stock_id}", headers=h)
    assert r.json()["code"] == 200, r.json()
    return float(r.json()["data"]["quantity"])


def test_consume_audit_deducts_once_and_rejects_double_audit(client):
    """单条领用并行/重复审批：库存最多扣一次，第二次得到明确业务错误"""
    h, stock_id = _setup_inventory(client, stock_qty=100)
    cid = _add_consume(client, h, stock_id, 30)

    r = _audit(client, h, "consume", cid)
    assert r.json()["code"] == 200, r.json()
    assert _stock_qty(client, h, stock_id) == 70.0

    # 第二次审核（并发场景中迟到的一方）：明确报错，库存不再扣
    r = _audit(client, h, "consume", cid)
    assert r.json()["code"] == 40076, r.json()
    assert _stock_qty(client, h, stock_id) == 70.0


def test_consume_insufficient_stock_rejects_and_keeps_pending(client):
    """审核时库存不足：审核通过失败，单据保持待审核（同事务回滚，不出现已通过但没扣库存）

    提交时库存充足（提交校验通过），审核前库存被其他领用耗尽（模拟并发扣减）。
    """
    h, stock_id = _setup_inventory(client, stock_qty=20)
    cid = _add_consume(client, h, stock_id, 15)  # 提交时 20 >= 15，通过

    # 审核前库存被并发领用降到 10（模拟另一笔已生效的扣减）
    from tests.conftest import TestingSessionLocal
    from app.modules.inventory.model import MaterialStock
    with TestingSessionLocal() as db:
        db.query(MaterialStock).filter(MaterialStock.id == stock_id).update({"quantity": 10})
        db.commit()

    r = _audit(client, h, "consume", cid)
    assert r.json()["code"] == 40072, r.json()
    assert _stock_qty(client, h, stock_id) == 10.0

    # 单据仍可解释地停留在待审核，补货后可再审
    r = client.get("/api/v1/inventory/consume/list?audit_status=待审核", headers=h)
    assert any(c["id"] == cid for c in r.json()["data"]["list"])

    with TestingSessionLocal() as db:
        db.query(MaterialStock).filter(MaterialStock.id == stock_id).update({"quantity": 20})
        db.commit()
    r = _audit(client, h, "consume", cid)
    assert r.json()["code"] == 200, r.json()
    assert _stock_qty(client, h, stock_id) == 5.0


def test_two_consumes_exceeding_stock_at_most_covered_pass(client):
    """两条待审领用合计超过库存：最多放行库存可覆盖的，另一条失败且库存不为负"""
    h, stock_id = _setup_inventory(client, stock_qty=10)
    c1 = _add_consume(client, h, stock_id, 6)
    c2 = _add_consume(client, h, stock_id, 6)

    assert _audit(client, h, "consume", c1).json()["code"] == 200
    r = _audit(client, h, "consume", c2)
    assert r.json()["code"] == 40072, r.json()
    qty = _stock_qty(client, h, stock_id)
    assert qty == 4.0 and qty >= 0

    # 失败那条保持待审核（可解释状态）
    r = client.get("/api/v1/inventory/consume/list?audit_status=待审核", headers=h)
    assert any(c["id"] == c2 for c in r.json()["data"]["list"])


def _add_purchase_and_audit(client, h, qty, price, name="玉米精料"):
    pid = _add_purchase(client, h, qty, price, name)
    r = _audit(client, h, "purchase", pid)
    assert r.json()["code"] == 200, r.json()
    return pid


def test_purchase_audit_syncs_stock_once_and_rejects_double_audit(client):
    """进货审核：只入一次库，重复审核报错，均价移动加权正确"""
    h, stock_id = _setup_inventory(client, stock_qty=0)

    pid = _add_purchase(client, h, 100, 3.2)
    assert _audit(client, h, "purchase", pid).json()["code"] == 200
    assert _stock_qty(client, h, stock_id) == 100.0

    # 重复审核
    r = _audit(client, h, "purchase", pid)
    assert r.json()["code"] == 40064, r.json()
    assert _stock_qty(client, h, stock_id) == 100.0

    # 第二批进货 100@4.8 → 总量 200，均价 (100*3.2+100*4.8)/200 = 4.0
    _add_purchase_and_audit(client, h, qty=100, price=4.8)
    assert _stock_qty(client, h, stock_id) == 200.0
    r = client.get(f"/api/v1/inventory/stock/{stock_id}", headers=h)
    assert abs(float(r.json()["data"]["unit_price"]) - 4.0) < 0.01

    # 不出现重复库存行（同名物资只有一条库存记录）
    r = client.get("/api/v1/inventory/stock/list?material_name=玉米精料", headers=h)
    assert r.json()["data"]["total"] == 1


def test_purchase_audit_revives_soft_deleted_stock_row(client):
    """撞上软删除的同名库存行（唯一键冲突恢复路径）：复活并累加，不再 500"""
    h, stock_id = _setup_inventory(client, stock_qty=0)
    # 直接软删该库存行，模拟"同名物资已删过、进货审核自动建档时撞唯一键"
    from tests.conftest import TestingSessionLocal
    from app.modules.inventory.model import MaterialStock
    with TestingSessionLocal() as db:
        db.query(MaterialStock).filter(MaterialStock.id == stock_id).update({"deleted": True})
        db.commit()

    pid = _add_purchase(client, h, 50, 3.0)
    r = _audit(client, h, "purchase", pid)
    assert r.json()["code"] == 200, r.json()
    assert _stock_qty(client, h, stock_id) == 50.0  # 复活的行数量正确


def test_consume_audit_rejects_when_stock_missing(client):
    """库存行被删（异常路径）：审核报错且回滚，状态回到待审核"""
    h, stock_id = _setup_inventory(client, stock_qty=10)
    cid = _add_consume(client, h, stock_id, 5)

    from tests.conftest import TestingSessionLocal
    from app.modules.inventory.model import MaterialStock
    with TestingSessionLocal() as db:
        db.query(MaterialStock).filter(MaterialStock.id == stock_id).update({"deleted": True})
        db.commit()

    r = _audit(client, h, "consume", cid)
    assert r.json()["code"] == 40077, r.json()

    # 单据状态回滚为待审核
    from app.modules.inventory.model import MaterialConsume
    with TestingSessionLocal() as db:
        c = db.query(MaterialConsume).filter(MaterialConsume.id == cid).first()
        assert c.audit_status == "待审核", c.audit_status
