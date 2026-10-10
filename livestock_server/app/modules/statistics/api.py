"""
统计路由（P3-1）

5 个只读统计接口，供数据大屏与统计分析页面使用：
- GET /statistics/dashboard  综合数据大屏
- GET /statistics/breeding   存栏繁育统计
- GET /statistics/health     防疫诊疗统计
- GET /statistics/material   物资消耗统计
- GET /statistics/finance    财务统计

权限：所有登录用户（统计面向全角色查看）
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import Result
from app.core.deps import get_current_user
from app.core.perms import require_perms
from app.core.exceptions import BizException
from app.models.user import User
from app.modules.statistics import service as statistics_service

# 模块级权限：统计口径（含财务统计）仅超管/场主，员工角色默认不含该模块
router = APIRouter(dependencies=[Depends(require_perms("statistics"))])


def _require_farm(current_user: User) -> int:
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)
    return current_user.farm_id


@router.get("/dashboard", summary="综合数据大屏（KPI + 存栏趋势 + 分布）")
def dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    return Result.ok(data=statistics_service.dashboard_stats(db, farm_id))


@router.get("/breeding", summary="存栏繁育统计")
def breeding(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    return Result.ok(data=statistics_service.breeding_stats(db, farm_id))


@router.get("/health", summary="防疫诊疗统计")
def health(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    return Result.ok(data=statistics_service.health_stats(db, farm_id))


@router.get("/material", summary="物资消耗统计")
def material(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    return Result.ok(data=statistics_service.material_stats(db, farm_id))


@router.get("/finance", summary="财务统计")
def finance(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    return Result.ok(data=statistics_service.finance_stats(db, farm_id))
