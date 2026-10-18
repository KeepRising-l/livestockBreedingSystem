"""
P1-B 验收：生产同款数据库（MySQL）下的真并发测试。

默认跳过；仅在设置了 TEST_MYSQL_URL 时运行，例如：

    TEST_MYSQL_URL="mysql+pymysql://root:密码@127.0.0.1:3306/livestock_test?charset=utf8mb4" \
        python -m pytest tests/test_concurrency_mysql.py -v

要求：TEST_MYSQL_URL 指向的库必须是**专用测试库**（会被反复建表/清库），
严禁指向开发或生产库。库需提前建好（空 schema 即可）。
"""
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import pytest

MYSQL_URL = os.environ.get("TEST_MYSQL_URL", "")

pytestmark = pytest.mark.skipif(
    not MYSQL_URL,
    reason="未设置 TEST_MYSQL_URL（需要专用 MySQL 测试库，不能指向开发/生产库）",
)


@pytest.fixture()
def mysql_session_factory():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database import Base
    import app.models  # noqa: F401

    engine = create_engine(MYSQL_URL, pool_pre_ping=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _seed(mysql_session_factory):
    """一个农场 + 一条 100kg 库存 + 待审领用/进货记录"""
    from app.models.farm import Farm
    from app.models.user import User
    from app.modules.pen.model import Pen
    from app.modules.inventory.model import MaterialStock, MaterialPurchase, MaterialConsume

    with mysql_session_factory() as db:
        farm = Farm(farm_name="并发测试场", owner_user_id=1, livestock_types="牛")
        db.add(farm)
        db.flush()
        stock = MaterialStock(farm_id=farm.id, material_type="饲料", material_name="并发精料",
                              quantity=100, unit="kg")
        db.add(stock)
        consume = MaterialConsume(farm_id=farm.id, stock_id=stock.id, material_type="饲料",
                                  material_name="并发精料", quantity=30, unit="kg",
                                  consume_date=date(2026, 8, 10), audit_status="待审核")
        db.add(consume)
        db.commit()
        return farm.id, stock.id, consume.id


def test_parallel_double_audit_consume_only_once(mysql_session_factory):
    """单条领用并行审批多次：库存最多扣一次，其余请求得到"已审核"业务结果"""
    from app.modules.inventory import service as inv
    from app.modules.inventory.schema import AuditActionIn

    farm_id, stock_id, consume_id = _seed(mysql_session_factory)

    def audit_once(_):
        with mysql_session_factory() as db:
            try:
                inv.audit_consume(db, farm_id, consume_id, AuditActionIn(audit_status="通过"))
                return "ok"
            except Exception as e:
                return f"err:{e}"

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(audit_once, range(8)))

    assert results.count("ok") == 1, results  # 恰好一次成功
    assert all(r.startswith("err:") for r in results if r != "ok")

    with mysql_session_factory() as db:
        from app.modules.inventory.model import MaterialStock
        stock = db.query(MaterialStock).filter(MaterialStock.id == stock_id).first()
        assert float(stock.quantity) == 70.0  # 只扣一次，不为负


def test_parallel_consumes_exceeding_stock_no_negative(mysql_session_factory):
    """两条待审领用合计超过库存，并行审批：最多放行库存可覆盖的，库存不为负"""
    from app.modules.inventory import service as inv
    from app.modules.inventory.schema import AuditActionIn
    from app.modules.inventory.model import MaterialConsume

    with mysql_session_factory() as db:
        from app.models.farm import Farm
        farm = Farm(farm_name="并发测试场2", owner_user_id=1, livestock_types="牛")
        db.add(farm)
        db.flush()
        from app.modules.inventory.model import MaterialStock
        stock = MaterialStock(farm_id=farm.id, material_type="饲料", material_name="并发精料",
                              quantity=10, unit="kg")
        db.add(stock)
        db.flush()
        ids = []
        for _ in range(2):
            c = MaterialConsume(farm_id=farm.id, stock_id=stock.id, material_type="饲料",
                                material_name="并发精料", quantity=6, unit="kg",
                                consume_date=date(2026, 8, 10), audit_status="待审核")
            db.add(c)
            db.flush()
            ids.append(c.id)
        db.commit()
        farm_id, stock_id = farm.id, stock.id

    def audit_once(cid):
        with mysql_session_factory() as db:
            try:
                inv.audit_consume(db, farm_id, cid, AuditActionIn(audit_status="通过"))
                return "ok"
            except Exception as e:
                return f"err:{e}"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(audit_once, ids))

    assert results.count("ok") == 1, results  # 6+6 > 10，只有一条能过

    with mysql_session_factory() as db:
        stock = db.query(MaterialStock).filter(MaterialStock.id == stock_id).first()
        qty = float(stock.quantity)
        assert qty == 4.0 and qty >= 0
        # 失败的那条保持待审核（可解释状态）
        pending = db.query(MaterialConsume).filter(
            MaterialConsume.farm_id == farm_id, MaterialConsume.audit_status == "待审核"
        ).count()
        assert pending == 1


def test_parallel_purchases_same_material_no_duplicate_or_loss(mysql_session_factory):
    """同物资并行进货审批（自动建档）：库存 = 两笔之和，只有一条库存行，无 500"""
    from app.modules.inventory import service as inv
    from app.modules.inventory.schema import AuditActionIn
    from app.modules.inventory.model import MaterialPurchase

    with mysql_session_factory() as db:
        from app.models.farm import Farm
        farm = Farm(farm_name="并发测试场3", owner_user_id=1, livestock_types="牛")
        db.add(farm)
        db.flush()
        ids = []
        for _ in range(2):
            p = MaterialPurchase(farm_id=farm.id, material_type="饲料", material_name="新物资",
                                 quantity=40, unit="kg", cost_price=3.0,
                                 purchase_date=date(2026, 8, 10), audit_status="待审核")
            db.add(p)
            db.flush()
            ids.append(p.id)
        db.commit()
        farm_id = farm.id

    def audit_once(pid):
        with mysql_session_factory() as db:
            try:
                inv.audit_purchase(db, farm_id, pid, AuditActionIn(audit_status="通过"))
                return "ok"
            except Exception as e:
                return f"err:{e}"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(audit_once, ids))

    assert all(r == "ok" for r in results), results  # 两笔都成功，无未处理 500

    with mysql_session_factory() as db:
        from app.modules.inventory.model import MaterialStock
        stocks = db.query(MaterialStock).filter(
            MaterialStock.farm_id == farm_id, MaterialStock.deleted == False
        ).all()
        assert len(stocks) == 1, "不应出现重复库存行"
        assert float(stocks[0].quantity) == 80.0  # 40 + 40，无丢失更新
        assert abs(float(stocks[0].unit_price) - 3.0) < 0.01
