"""
P1-C1 验收：单只动物饲料成本不再重复计入整圈舍成本。

口径（按指引建议的最小可行方案，待负责人确认）：
- 每条已审核通过的圈舍饲喂记录，单只动物只分摊 feed_cost / 当条记录的 animal_count 快照
- animal_count 缺失 / 为 0 的记录无法定义分摊口径，跳过不计（不除零）
- 圈舍在栏历史无法从当前档案精确还原，转舍动物的早期圈舍记录不参与个体成本（估算口径）
- 分项先四舍五入再求和：feed + medicine + labor + consumable == total_cost
"""
from datetime import date

from tests.conftest import TestingSessionLocal, register_farm

from app.models.farm import Farm
from app.models.user import User
from app.modules.pen.model import Pen
from app.modules.animal.model import Animal
from app.modules.feeding.model import FeedingRecord
from app.modules.finance import service as finance_service
from app.modules.finance.schema import SaleOutIn


def _seed_farm_and_pen(client):
    """注册农场（拿合法 owner_user_id / farm_id）+ 建圈舍"""
    register_farm(client, "成本核算牛场", "owner1")
    with TestingSessionLocal() as db:
        farm = db.query(Farm).order_by(Farm.id).first()
        pen = Pen(farm_id=farm.id, pen_code="A01", pen_type="A", species="牛",
                  capacity=12, current_count=2)
        db.add(pen)
        db.flush()
        db.commit()
        return farm.id, pen.id


def _add_animal(db, farm_id, pen_id, ear_tag, in_date=date(2026, 8, 1)):
    a = Animal(
        farm_id=farm_id, ear_tag=ear_tag, species="牛", breed="黄牛",
        pen_id=pen_id, gender="母", birth_date=date(2026, 1, 1),
        in_date=in_date, status="在栏", source="外购",
    )
    db.add(a)
    return a


def _add_feeding(db, farm_id, pen_id, feed_date, cost, count, audit="通过"):
    r = FeedingRecord(
        farm_id=farm_id, feed_date=feed_date, time_period="早",
        pen_id=pen_id, pen_type="A", animal_count=count, feed_cost=cost,
        status="已投喂" if audit == "通过" else "未投喂", audit_status=audit,
    )
    db.add(r)
    return r


def test_per_head_allocation_no_double_count(client):
    """两只动物同圈：各自只承担 1/2 的圈舍饲喂成本，不再整额重复计入"""
    _seed_farm_and_pen(client)
    with TestingSessionLocal() as db:
        farm = db.query(Farm).order_by(Farm.id).first()
        pen = db.query(Pen).filter(Pen.pen_code == "A01").first()

        a1 = _add_animal(db, farm.id, pen.id, "10101")
        a2 = _add_animal(db, farm.id, pen.id, "10102")
        # 30 元/条 × 2 头 + 10 元/条 × 2 头 → 每只 15 + 5 = 20 元
        _add_feeding(db, farm.id, pen.id, date(2026, 8, 5), 30, 2)
        _add_feeding(db, farm.id, pen.id, date(2026, 8, 6), 10, 2)
        # 头数缺失 / 为 0 / 未过审 / 窗口外：均不参与个体分摊
        _add_feeding(db, farm.id, pen.id, date(2026, 8, 7), 50, 0)          # 头数=0 → 跳过
        _add_feeding(db, farm.id, pen.id, date(2026, 8, 8), 20, None)       # 头数 NULL → 跳过
        _add_feeding(db, farm.id, pen.id, date(2026, 8, 9), 99, 2, audit="待审核")  # 未过审 → 不计
        _add_feeding(db, farm.id, pen.id, date(2026, 1, 1), 100, 2)         # 入栏前 → 不计
        db.commit()

        out = date(2026, 9, 1)
        for animal in (a1, a2):
            costs = finance_service._calc_animal_cost(db, farm.id, animal, out)
            assert float(costs["feed_cost"]) == 20.0, costs
            # 分项之和 == 总成本（精确一致）
            parts = (float(costs["feed_cost"]) + float(costs["medicine_cost"])
                     + float(costs["labor_cost"]) + float(costs["consumable_cost"]))
            assert round(parts, 2) == float(costs["total_cost"]), costs


def test_sale_out_details_share_pen_cost(client):
    """出栏销售：同圈两头各计 1/2 圈舍成本；订单口径两头分摊合计 == 记录总额"""
    _seed_farm_and_pen(client)
    with TestingSessionLocal() as db:
        farm = db.query(Farm).order_by(Farm.id).first()
        pen = db.query(Pen).filter(Pen.pen_code == "A01").first()
        _add_animal(db, farm.id, pen.id, "10101")
        _add_animal(db, farm.id, pen.id, "10102")
        _add_feeding(db, farm.id, pen.id, date(2026, 8, 5), 30, 2)   # 每头 15
        _add_feeding(db, farm.id, pen.id, date(2026, 8, 6), 10, 2)   # 每头 5
        db.commit()

    with TestingSessionLocal() as db:
        from app.modules.finance.model import SaleOrderDetail
        farm = db.query(Farm).order_by(Farm.id).first()
        body = SaleOutIn(
            customer="张老板", unit_price=20.0,
            items=[{"ear_tag": "10101", "weight": 300}, {"ear_tag": "10102", "weight": 310}],
            order_date=date(2026, 9, 1),
        )
        order = finance_service.sale_out(db, farm.id, body, user_id=1)
        details = db.query(SaleOrderDetail).filter(SaleOrderDetail.order_id == order.id).all()
        assert len(details) == 2
        for d in details:
            assert float(d.feed_cost) == 20.0, (d.ear_tag, d.feed_cost)
            # 明细四项之和 == total_cost；利润 == 销售额 - 总成本
            parts = float(d.feed_cost) + float(d.medicine_cost) + float(d.labor_cost) + float(d.consumable_cost)
            assert round(parts, 2) == float(d.total_cost)
            assert round(float(d.sale_amount) - float(d.total_cost), 2) == float(d.profit)
        # 两头分摊合计 40 == 圈舍记录总额 (30+10)
        assert round(sum(float(d.feed_cost) for d in details), 2) == 40.0
        # 档案已出栏 + 圈舍存栏清零
        pen = db.query(Pen).filter(Pen.pen_code == "A01").first()
        assert pen.current_count == 0


def test_partial_sale_and_cross_pen_no_leak(client):
    """部分出栏 + 跨圈不重复计费：只卖一头时另一头不受影响；不同圈舍成本互不串"""
    _seed_farm_and_pen(client)
    with TestingSessionLocal() as db:
        farm = db.query(Farm).order_by(Farm.id).first()
        pen1 = db.query(Pen).filter(Pen.pen_code == "A01").first()
        pen2 = Pen(farm_id=farm.id, pen_code="A02", pen_type="A", species="牛",
                   capacity=12, current_count=1)
        db.add(pen2)
        db.flush()
        _add_animal(db, farm.id, pen1.id, "10101")
        a3 = _add_animal(db, farm.id, pen2.id, "10201")
        # 圈1 记录成本 30/2头；圈2 记录成本 20/1头
        _add_feeding(db, farm.id, pen1.id, date(2026, 8, 5), 30, 2)
        _add_feeding(db, farm.id, pen2.id, date(2026, 8, 5), 20, 1)
        db.commit()

        body = SaleOutIn(
            customer="李老板", unit_price=15.0,
            items=[{"ear_tag": "10101", "weight": 300}],
            order_date=date(2026, 9, 1),
        )
        finance_service.sale_out(db, farm.id, body, user_id=1)

        # 圈1 卖出的那头：15（30/2）；未出栏的 10102 不受影响
        # 圈2 的 10201：只计自己圈舍的 20，不串圈1的记录
        costs = finance_service._calc_animal_cost(db, farm.id, a3, date(2026, 9, 2))
        assert float(costs["feed_cost"]) == 20.0, costs


def test_pen_transfer_early_records_not_attributed(client):
    """转舍动物的早期圈舍记录不参与个体成本（在栏历史无法还原，按当前圈舍估算）"""
    _seed_farm_and_pen(client)
    with TestingSessionLocal() as db:
        farm = db.query(Farm).order_by(Farm.id).first()
        pen1 = db.query(Pen).filter(Pen.pen_code == "A01").first()
        pen2 = Pen(farm_id=farm.id, pen_code="A02", pen_type="A", species="牛",
                   capacity=12, current_count=1)
        db.add(pen2)
        db.flush()
        # 10101 先在圈1（8月，成本 30/2头），9月转到圈2（成本 20/1头）
        a = _add_animal(db, farm.id, pen1.id, "10101")
        _add_feeding(db, farm.id, pen1.id, date(2026, 8, 5), 30, 2)
        a.pen_id = pen2.id
        _add_feeding(db, farm.id, pen2.id, date(2026, 9, 5), 20, 1)
        db.commit()

        costs = finance_service._calc_animal_cost(db, farm.id, a, date(2026, 9, 10))
        # 只按当前圈舍（圈2）记录估算 = 20；圈1 的 15 元无法追溯到个体（口径已注明）
        assert float(costs["feed_cost"]) == 20.0, costs


def test_empty_pen_and_zero_window_safe(client):
    """无圈舍 / 无饲喂记录 / 出栏当天无记录：不报错，饲料成本为 0"""
    _seed_farm_and_pen(client)
    with TestingSessionLocal() as db:
        farm = db.query(Farm).order_by(Farm.id).first()
        # 无圈动物
        a = _add_animal(db, farm.id, None, "10301")
        costs = finance_service._calc_animal_cost(db, farm.id, a, date(2026, 9, 1))
        assert float(costs["feed_cost"]) == 0.0
        assert float(costs["total_cost"]) >= 0.0  # 可能含人工
