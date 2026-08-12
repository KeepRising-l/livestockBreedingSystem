"""
v1 版本路由聚合
所有 v1 接口在这里挂载，前缀 /api/v1

说明：模块化重构后，业务模块的路由收敛到 app/modules/*/api.py，
      api/v1/__init__.py 只负责把各模块的 router 挂到统一前缀下。
      后续新模块（breeding / review / statistics 等）在此追加一行即可。
"""
from fastapi import APIRouter

from app.api.v1 import auth, farm
from app.modules.pen import router as pen_router
from app.modules.animal import router as animal_router
from app.modules.feeding import router as feeding_router
from app.modules.inventory import router as inventory_router
from app.modules.system import router as system_router
from app.modules.health import router as health_router
from app.modules.breeding import router as breeding_router
from app.modules.review import router as review_router
from app.modules.salary import router as salary_router
from app.modules.finance import router as finance_router
from app.modules.statistics import router as statistics_router

router = APIRouter(prefix="/v1")
router.include_router(auth.router, prefix="/auth", tags=["认证模块"])
router.include_router(farm.router, prefix="/farm", tags=["养殖场模块"])
router.include_router(pen_router, prefix="/pen", tags=["圈舍模块"])
router.include_router(animal_router, prefix="/animal", tags=["档案模块"])
router.include_router(feeding_router, prefix="/feeding", tags=["饲喂模块"])
router.include_router(inventory_router, prefix="/inventory", tags=["物资库存模块"])
router.include_router(system_router, prefix="/system", tags=["系统管理模块"])
router.include_router(health_router, prefix="/health", tags=["防疫诊疗模块"])
router.include_router(breeding_router, prefix="/breeding", tags=["繁育模块"])
router.include_router(review_router, prefix="/review", tags=["审核模块"])
router.include_router(salary_router, prefix="/salary", tags=["薪资配置模块"])
router.include_router(finance_router, prefix="/finance", tags=["销售财务模块"])
router.include_router(statistics_router, prefix="/statistics", tags=["统计模块"])
