"""
定时任务模块（APScheduler）

每日 4 个任务（北京时间凌晨执行）：
- 00:05 refresh_growth_stages        刷新所有在栏畜禽的生长阶段
- 00:10 scan_breeding_alerts         自动生成繁育预警（孕检/临产/未发情）
- 00:20 refresh_material_stock_status 刷新物资库存的过期/缺货状态
- 00:30 clean_animal_history         清理超过 180 天的历史档案记录

调度器在 app.main.lifespan 中启动/关闭（start_scheduler / shutdown_scheduler）。
"""
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app.database import SessionLocal
from app.modules.animal.model import Animal, AnimalHistory
from app.modules.animal.service import calc_age_days, determine_growth_stage
from app.modules.breeding.model import MatingRecord, BirthRecord, BreedingAlert
from app.modules.inventory.service import refresh_all_stock_status

# 预警规则常量（天）
PREGNANCY_CHECK_DAYS = 60   # 配种后满 60 天 → 孕检提醒
BIRTH_REMIND_DAYS = 15      # 预产期前 15 天 → 临产提醒
HEAT_REMIND_DAYS = 60       # 产犊后满 60 天仍无配种 → 未发情提醒
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

def _alert_exists(db, farm_id: int, animal_tag: str, alert_type: str, alert_date: date) -> bool:
    """同一天同一耳标同一类型预警已存在则跳过，避免重复生成"""
    return db.query(BreedingAlert).filter(
        BreedingAlert.farm_id == farm_id,
        BreedingAlert.animal_tag == animal_tag,
        BreedingAlert.alert_type == alert_type,
        BreedingAlert.alert_date == alert_date,
    ).first() is not None


def scan_breeding_alerts():
    """生成 3 类繁育预警：孕检/临产/未发情（同耳标同类型同日期去重）"""
    db = SessionLocal()
    try:
        today = date.today()
        created = 0

        # 1. 孕检提醒：配种后满 60 天仍未孕检
        check_line = today - timedelta(days=PREGNANCY_CHECK_DAYS)
        matings = db.query(MatingRecord).filter(
            MatingRecord.deleted == False,
            MatingRecord.status == "待孕检",
            MatingRecord.mating_date <= check_line,
        ).all()
        for m in matings:
            if _alert_exists(db, m.farm_id, m.female_tag, "孕检", today):
                continue
            db.add(BreedingAlert(
                farm_id=m.farm_id,
                alert_type="孕检",
                animal_tag=m.female_tag,
                related_id=m.id,
                alert_date=today,
                alert_content=f"耳标 {m.female_tag} 配种已满 {PREGNANCY_CHECK_DAYS} 天，请尽快安排孕检（配种日期 {m.mating_date}）",
                status="待处理",
            ))
            created += 1

        # 2. 临产提醒：预产期距今天 ≤ 15 天
        remind_line = today + timedelta(days=BIRTH_REMIND_DAYS)
        pregnant = db.query(MatingRecord).filter(
            MatingRecord.deleted == False,
            MatingRecord.status == "成功怀孕",
            MatingRecord.expected_birth_date.isnot(None),
            MatingRecord.expected_birth_date >= today,
            MatingRecord.expected_birth_date <= remind_line,
        ).all()
        for m in pregnant:
            if _alert_exists(db, m.farm_id, m.female_tag, "临产", today):
                continue
            remain = (m.expected_birth_date - today).days
            db.add(BreedingAlert(
                farm_id=m.farm_id,
                alert_type="临产",
                animal_tag=m.female_tag,
                related_id=m.id,
                alert_date=today,
                alert_content=f"耳标 {m.female_tag} 预产期 {m.expected_birth_date}，剩余 {remain} 天，请提前准备接产",
                status="待处理",
            ))
            created += 1

        # 3. 未发情提醒：产犊后满 60 天仍无下一次配种记录
        heat_line = today - timedelta(days=HEAT_REMIND_DAYS)
        births = db.query(BirthRecord).filter(
            BirthRecord.deleted == False,
            BirthRecord.birth_date <= heat_line,
        ).all()
        for b in births:
            later_mating = db.query(MatingRecord).filter(
                MatingRecord.farm_id == b.farm_id,
                MatingRecord.female_tag == b.female_tag,
                MatingRecord.deleted == False,
                MatingRecord.mating_date >= b.birth_date,
            ).first()
            if later_mating:
                continue
            if _alert_exists(db, b.farm_id, b.female_tag, "未发情", today):
                continue
            db.add(BreedingAlert(
                farm_id=b.farm_id,
                alert_type="未发情",
                animal_tag=b.female_tag,
                related_id=b.id,
                alert_date=today,
                alert_content=f"耳标 {b.female_tag} 产犊已满 {HEAT_REMIND_DAYS} 天仍未配种，请关注发情情况（产犊日期 {b.birth_date}）",
                status="待处理",
            ))
            created += 1

        db.commit()
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
