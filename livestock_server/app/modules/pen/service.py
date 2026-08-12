"""
圈舍业务逻辑

核心算法：圈舍自动分配
- 根据生长阶段判定应入哪类圈舍（A/B/C/D）
- 找到该类型下有空位的圈舍，按编号排序，依次分配
"""
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.core.utils import get_effective_farm_id
from app.modules.pen.model import Pen
from app.modules.pen.schema import PenAddIn, PenUpdateIn


# 生长阶段 -> 圈舍类型映射
STAGE_TO_PEN_TYPE = {
    "犊牛期": "A", "羔羊期": "A", "仔猪期": "A",
    "保育期": "A",
    "生长期": "B",
    "育肥期": "B",
    "繁育期": "C",
    "妊娠期": "C",
    "种用": "D",
}

# 圈舍类型默认容量
DEFAULT_CAPACITY = {
    "A": 12,
    "B": 12,
    "C": 6,
    "D": 1,
}


def list_pens(db: Session, farm_id: int, pen_type: str = None, species: str = None,
              status: int = None, page_num: int = 1, page_size: int = 10) -> dict:
    """圈舍列表"""
    fid = get_effective_farm_id(db, farm_id)
    query = db.query(Pen).filter(Pen.farm_id == fid, Pen.deleted == False)
    if pen_type:
        query = query.filter(Pen.pen_type == pen_type)
    if species:
        # 只返回圈养了该畜种畜禽的圈舍（延迟导入避免与 animal.service 循环依赖）
        from app.modules.animal.model import Animal
        # 只返回圈养了该畜种畜禽的圈舍
        pen_ids = db.query(Animal.pen_id).filter(
            Animal.farm_id == fid, Animal.species == species, Animal.deleted == False
        ).distinct().all()
        ids = [r[0] for r in pen_ids if r[0] is not None]
        query = query.filter(Pen.id.in_(ids) if ids else False)
    if status is not None:
        query = query.filter(Pen.status == status)
    total = query.count()
    items = query.order_by(Pen.pen_code).offset((page_num - 1) * page_size).limit(page_size).all()
    return {"list": items, "total": total, "pageNum": page_num, "pageSize": page_size}


def get_pen(db: Session, farm_id: int, pen_id: int) -> Pen:
    fid = get_effective_farm_id(db, farm_id)
    pen = db.query(Pen).filter(
        Pen.id == pen_id, Pen.farm_id == fid, Pen.deleted == False
    ).first()
    if not pen:
        raise BizException("圈舍不存在", code=40010)
    return pen


def add_pen(db: Session, farm_id: int, body: PenAddIn) -> Pen:
    """新增圈舍"""
    fid = get_effective_farm_id(db, farm_id)
    if body.pen_type not in ("A", "B", "C", "D"):
        raise BizException("圈舍类型必须是 A/B/C/D", code=40011)
    exists = db.query(Pen).filter(
        Pen.farm_id == fid, Pen.pen_code == body.pen_code, Pen.deleted == False
    ).first()
    if exists:
        raise BizException("圈舍编号已存在", code=40012)
    pen = Pen(
        farm_id=fid,
        pen_code=body.pen_code,
        pen_type=body.pen_type,
        capacity=body.capacity,
        current_count=0,
        status=1,
        remark=body.remark,
    )
    db.add(pen)
    db.commit()
    return pen


def update_pen(db: Session, farm_id: int, pen_id: int, body: PenUpdateIn) -> Pen:
    pen = get_pen(db, farm_id, pen_id)
    if body.pen_code is not None:
        pen.pen_code = body.pen_code
    if body.pen_type is not None:
        pen.pen_type = body.pen_type
    if body.capacity is not None:
        if body.capacity < pen.current_count:
            raise BizException("新容量不能小于当前存栏数", code=40013)
        pen.capacity = body.capacity
    if body.status is not None:
        pen.status = body.status
    if body.remark is not None:
        pen.remark = body.remark
    db.commit()
    return pen


def delete_pen(db: Session, farm_id: int, pen_id: int):
    pen = get_pen(db, farm_id, pen_id)
    if pen.current_count > 0:
        raise BizException("圈舍内有畜禽，不能删除", code=40014)
    pen.deleted = True
    db.commit()


def find_available_pen(db: Session, farm_id: int, pen_type: str) -> Pen:
    """
    找一个有空位的圈舍（自动分配算法核心）
    按圈舍编号升序找第一个未满的圈舍
    """
    fid = get_effective_farm_id(db, farm_id)
    pen = db.query(Pen).filter(
        Pen.farm_id == fid,
        Pen.pen_type == pen_type,
        Pen.deleted == False,
        Pen.status == 1,
        Pen.current_count < Pen.capacity,
    ).order_by(Pen.pen_code).first()

    if not pen:
        raise BizException(f"类型 {pen_type} 的圈舍已满，请先添加圈舍", code=40015)
    return pen
