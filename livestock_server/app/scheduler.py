"""
定时任务模块（APScheduler）

每日 4 个任务（北京时间凌晨执行）：
- 00:05 refresh_growth_stages        刷新所有在栏畜禽的生长阶段
- 00:10 scan_breeding_alerts         自动生成繁育预警（规则见 breeding.service.ensure_alerts；
                                      繁育预警列表接口也会按需生成，定时任务只兜底）
- 00:20 refresh_material_stock_status 刷新物资库存的过期/缺货状态
- 00:30 clean_animal_history         清理超过 180 天的历史档案记录

调度器在 app.main.lifespan 中启动/关闭（start_scheduler / shutdown_scheduler）。
"""
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app.database import SessionLocal
from app.models.farm import Farm
from app.modules.animal.model import Animal, AnimalHistory
from app.modules.animal.service import calc_age_days, determine_growth_stage
from app.modules.breeding.service import ensure_alerts
from app.modules.inventory.service import refresh_all_stock_status

HISTORY_CLEAN_DAYS = 180    # 历史档案保留 180 天后清除

# 需要参与生长阶段刷新的档案状态（在栏/种用/隔离/待出栏）
ACTIVE_STATUSES = ("在栏", "种用", "隔离", "待出栏")


def _log(msg: str):
    print(f"[定时任务] {msg}")


# ============================================================
# 1. 每日刷新生长阶段
# ============================================================

def refresh_growth_stages():
    """按出生日期 + 畜种重算所有在栏畜禽的生长阶段（妊娠期由配种记录标记，不覆盖）"""
    db = SessionLocal()
    try:
        today = date.today()
        animals = db.query(Animal).filter(
            Animal.deleted == False,
            Animal.status.in_(ACTIVE_STATUSES),
        ).all()
        changed = 0
        for a in animals:
            if a.growth_stage == "妊娠" or not a.birth_date:
                continue
            age_days = calc_age_days(a.birth_date, today)
            new_stage = determine_growth_stage(a.species, age_days)
            if new_stage != a.growth_stage:
                a.growth_stage = new_stage
                changed += 1
        db.commit()
        _log(f"生长阶段刷新完成，扫描 {len(animals)} 只，更新 {changed} 只")
    except Exception as e:
        db.rollback()
        _log(f"生长阶段刷新失败：{e}")
    finally:
        db.close()


# ============================================================
# 2. 每日自动生成繁育预警
# ============================================================

def scan_breeding_alerts():
    """逐养殖场生成繁育预警（规则统一由 breeding.service.ensure_alerts 实现）"""
    db = SessionLocal()
    try:
        farm_ids = [row[0] for row in db.query(Farm.id).filter(Farm.deleted == False).all()]
        created = 0
        for farm_id in farm_ids:
            created += ensure_alerts(db, farm_id)
        _log(f"繁育预警扫描完成，新生成 {created} 条")
    except Exception as e:
        db.rollback()
        _log(f"繁育预警扫描失败：{e}")
    finally:
        db.close()


# ============================================================
# 3. 每日刷新物资库存状态
# ============================================================

def refresh_material_stock_status():
    """刷新所有库存的即将过期/已过期/缺货状态"""
    db = SessionLocal()
    try:
        changed = refresh_all_stock_status(db)
        _log(f"库存状态刷新完成，状态变化 {changed} 条")
    except Exception as e:
        db.rollback()
        _log(f"库存状态刷新失败：{e}")
    finally:
        db.close()


# ============================================================
# 4. 每日清理历史档案记录
# ============================================================

def clean_animal_history():
    """物理删除 delete_time 距今超过 180 天的历史档案记录"""
    db = SessionLocal()
    try:
        deadline = date.today() - timedelta(days=HISTORY_CLEAN_DAYS)
        count = db.query(AnimalHistory).filter(
            AnimalHistory.deleted == False,
            AnimalHistory.delete_time.isnot(None),
            AnimalHistory.delete_time < deadline,
        ).delete(synchronize_session=False)
        db.commit()
        _log(f"历史记录清理完成，删除 {count} 条（保留 {HISTORY_CLEAN_DAYS} 天）")
    except Exception as e:
        db.rollback()
        _log(f"历史记录清理失败：{e}")
    finally:
        db.close()


# ============================================================
# 调度器（在 main.py lifespan 中启停）
# ============================================================

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def start_scheduler():
    """启动调度器并注册 4 个每日任务（幂等，重复调用不会重复注册）"""
    if scheduler.running:
        return
    scheduler.add_job(refresh_growth_stages, "cron", hour=0, minute=5,
                      id="refresh_growth_stages", replace_existing=True)
    scheduler.add_job(scan_breeding_alerts, "cron", hour=0, minute=10,
                      id="scan_breeding_alerts", replace_existing=True)
    scheduler.add_job(refresh_material_stock_status, "cron", hour=0, minute=20,
                      id="refresh_material_stock_status", replace_existing=True)
    scheduler.add_job(clean_animal_history, "cron", hour=0, minute=30,
                      id="clean_animal_history", replace_existing=True)
    scheduler.start()
    _log("调度器已启动，4 个每日任务已注册（00:05/00:10/00:20/00:30）")


def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        _log("调度器已停止")
