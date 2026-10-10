"""
薪资配置路由

按岗位配置基础薪资 / 奖金比例 / 扣罚规则。
权限：仅养殖场主/超管（侧边栏菜单 roles [1,2]），员工无薪资配置权限。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import Result
from app.core.deps import get_current_user
from app.core.perms import require_perms
from app.core.exceptions import BizException
from app.models.user import User
from app.modules.salary import service as salary_service
from app.modules.salary.schema import (
    SalaryConfigIn, SalaryConfigUpdateIn, SalaryConfigOut, SalaryConfigQuery,
)

# 模块级权限：薪资「配置」挂在前端「养殖场管理」下（farm/salary），故用 farm 权限，
# 与 finance 模块下的薪资「记录」（finance/salary）区分开
router = APIRouter(dependencies=[Depends(require_perms("farm"))])


def _check_owner(current_user: User):
    """养殖场主或超管才能配置薪资（user_type=1 或 2）"""
    if current_user.user_type not in (1, 2):
        raise BizException("无权限操作，需养殖场主权限", code=40301)
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)


@router.get("/list", summary="薪资配置列表（分页 + 岗位/状态筛选）")
def list_configs(
    post: str = Query(None),
    status: int = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_owner(current_user)
    query = SalaryConfigQuery(post=post, status=status, pageNum=pageNum, pageSize=pageSize)
    result = salary_service.list_configs(db, current_user.farm_id, query)
    result["list"] = [SalaryConfigOut.model_validate(r) for r in result["list"]]
    return Result.ok(data=result)


@router.get("/{config_id}", summary="薪资配置详情")
def get_config(config_id: int, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    conf = salary_service.get_config(db, current_user.farm_id, config_id)
    return Result.ok(data=SalaryConfigOut.model_validate(conf))


@router.post("/add", summary="新增薪资配置")
def add_config(body: SalaryConfigIn, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    conf = salary_service.add_config(db, current_user.farm_id, body)
    return Result.ok(data=SalaryConfigOut.model_validate(conf), msg="新增成功")


@router.put("/{config_id}", summary="修改薪资配置（岗位不可改）")
def update_config(config_id: int, body: SalaryConfigUpdateIn, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    conf = salary_service.update_config(db, current_user.farm_id, config_id, body)
    return Result.ok(data=SalaryConfigOut.model_validate(conf), msg="修改成功")


@router.delete("/{config_id}", summary="删除薪资配置")
def delete_config(config_id: int, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    salary_service.delete_config(db, current_user.farm_id, config_id)
    return Result.ok(msg="删除成功")
