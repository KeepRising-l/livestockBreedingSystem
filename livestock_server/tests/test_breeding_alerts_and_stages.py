"""
繁育模块回归测试：

1. 繁育预警改为「按需生成 + 幂等」：打开列表即可看到临产预警（含已逾期），
   重复调用不新增；新建临产预警给场主推送一条站内消息，重复调用不重复推送。
2. 母畜/公畜档案按出生日期实时算日龄：
   growth_stage 为繁育口径（繁育期/妊娠），real_growth_stage 为档案真实阶段（育肥期）。
"""
from datetime import date, timedelta

from tests.conftest import TestingSessionLocal, register_farm

from app import scheduler as scheduler_module
from app.models.farm import Farm
from app.models.user import User
from app.modules.animal.model import Animal
from app.modules.animal.service import GESTATION_DAYS
from app.modules.breeding import service as breeding_service
from app.modules.breeding.model import BirthRecord, BreedingAlert, MatingRecord
from app.modules.system.model import SysMessage

SPECIES = "牛"
GESTATION = GESTATION_DAYS[SPECIES]


# ===== 辅助 =====

def _farm_id(farm_name: str) -> int:
    with TestingSessionLocal() as db:
        farm = db.query(Farm).filter(
            Farm.farm_name == farm_name, Farm.deleted == False
        ).one()
        return farm.id


def _create_pen(client, headers, pen_code: str = "A01", capacity: int = 20) -> int:
    r = client.post("/api/v1/pen/add", json={
        "pen_code": pen_code, "pen_type": "A", "capacity": capacity,
    }, headers=headers)
    body = r.json()
    assert body["code"] == 200, body
    return body["data"]["id"]


def _create_animal(client, headers, pen_id: int, birth_date: date,
                   gender: str = "母") -> dict:
    r = client.post("/api/v1/animal/individual", json={
        "species": SPECIES, "breed": "黄牛", "gender": gender,
        "birth_date": birth_date.isoformat(),
        "in_date": date.today().isoformat(),
        "source": "外购", "pen_id": pen_id,
    }, headers=headers)
    body = r.json()
    assert body["code"] == 200, body
    return body["data"]


def _set_stored_stage(ear_tag: str, stage: str) -> None:
    """模拟每日 00:05 刷新前的陈旧存储值（验证接口按出生日期实时判定）"""
    with TestingSessionLocal() as db:
        db.query(Animal).filter(Animal.ear_tag == ear_tag).update({"growth_stage": stage})
        db.commit()


def _seed_pregnant_mating(farm_id: int, female_tag: str, expected_birth_date: date) -> int:
    """造一条已审核通过、成功怀孕的配种记录，返回记录 ID"""
    with TestingSessionLocal() as db:
        rec = MatingRecord(
            farm_id=farm_id,
            female_tag=female_tag,
            species=SPECIES,
            mating_date=expected_birth_date - timedelta(days=GESTATION),
            mating_type="本交",
            status="成功怀孕",
            audit_status="通过",
            expected_birth_date=expected_birth_date,
            gestation_days=GESTATION,
        )
        db.add(rec)
        db.commit()
        return rec.id


def _seed_pending_check_mating(farm_id: int, female_tag: str, mating_date: date) -> int:
    """造一条已审核通过、待孕检的配种记录，返回记录 ID"""
    with TestingSessionLocal() as db:
        rec = MatingRecord(
            farm_id=farm_id,
            female_tag=female_tag,
            species=SPECIES,
            mating_date=mating_date,
            mating_type="本交",
            status="待孕检",
            audit_status="通过",
            expected_birth_date=mating_date + timedelta(days=GESTATION),
            gestation_days=GESTATION,
        )
        db.add(rec)
        db.commit()
        return rec.id


def _seed_birth(farm_id: int, female_tag: str, birth_date: date) -> int:
    """造一条产犊记录，返回记录 ID"""
    with TestingSessionLocal() as db:
        rec = BirthRecord(
            farm_id=farm_id,
            female_tag=female_tag,
            species=SPECIES,
            birth_date=birth_date,
            total_count=1,
            alive_count=1,
            dead_count=0,
            survival_rate=100,
        )
        db.add(rec)
        db.commit()
        return rec.id


# ===== 母畜 / 公畜档案字段口径 =====

def test_female_list_uses_realtime_age_and_breeding_stage(client):
    """373 日龄母牛：即使存储的 growth_stage 陈旧为生长期，也要显示繁育期 + 真实育肥期"""
    farm_name = "繁育口径牛场"
    headers = register_farm(client, farm_name, "stage_owner")
    today = date.today()
    pen_id = _create_pen(client, headers)

    birth_date = today - timedelta(days=373)
    old = _create_animal(client, headers, pen_id, birth_date)
    # 200 日龄母牛未达可繁育日龄（牛 365），不应出现在繁育档案
    _create_animal(client, headers, pen_id, today - timedelta(days=200))
    _set_stored_stage(old["ear_tag"], "生长期")

    r = client.get("/api/v1/breeding/females", params={
        "species": SPECIES, "pageSize": 100,
    }, headers=headers)
    body = r.json()
    assert body["code"] == 200, body
    data = body["data"]
    assert data["total"] == 1, data
    row = data["list"][0]
    assert row["ear_tag"] == old["ear_tag"]
    assert row["age_days"] == 373
    assert row["growth_stage"] == "繁育期"
    assert row["real_growth_stage"] == "育肥期"
    # 前端已用字段不能被破坏
    assert row["birth_date"] == birth_date.isoformat()
    assert row["species"] == SPECIES
    assert row["breed"] == "黄牛"
    assert row["gender"] == "母"
    assert row["pen_id"] == pen_id
    assert row["status"] == "在栏"
    assert "physio_status" in row

    # 妊娠个体：繁育口径显示妊娠，档案真实阶段仍是育肥期
    r = client.put(
        f"/api/v1/breeding/females/{old['ear_tag']}/physio-status",
        json={"physio_status": "妊娠"}, headers=headers,
    )
    assert r.json()["code"] == 200, r.json()

    r = client.get("/api/v1/breeding/females", params={
        "species": SPECIES, "pageSize": 100,
    }, headers=headers)
    row = r.json()["data"]["list"][0]
    assert row["growth_stage"] == "妊娠"
    assert row["real_growth_stage"] == "育肥期"
    assert row["physio_status"] == "妊娠"


def test_male_list_uses_realtime_age_and_breeding_stage(client):
    """公畜列表同样补日龄 + 繁育口径阶段 + 真实阶段"""
    farm_name = "公畜口径牛场"
    headers = register_farm(client, farm_name, "male_stage_owner")
    today = date.today()
    pen_id = _create_pen(client, headers)

    male = _create_animal(client, headers, pen_id, today - timedelta(days=373), gender="公")
    _set_stored_stage(male["ear_tag"], "生长期")

    r = client.get("/api/v1/breeding/males", params={
        "species": SPECIES, "pageSize": 100,
    }, headers=headers)
    body = r.json()
    assert body["code"] == 200, body
    data = body["data"]
    assert data["total"] == 1, data
    row = data["list"][0]
    assert row["ear_tag"] == male["ear_tag"]
    assert row["age_days"] == 373
    assert row["growth_stage"] == "繁育期"
    assert row["real_growth_stage"] == "育肥期"
    # 公畜健康档案字段仍然保留
    assert row["health_status"] == "健康"
    assert row["mating_count"] == 0
    assert row["success_count"] == 0


# ===== 繁育预警：按需生成 + 幂等 =====

def test_alert_list_generates_overdue_and_upcoming_alerts_idempotently(client):
    """打开预警列表即生成临产预警；已逾期的也要有；重复打开不新增、不串场"""
    farm_name = "预警牛场"
    headers = register_farm(client, farm_name, "alert_owner")
    today = date.today()
    pen_id = _create_pen(client, headers)

    upcoming = _create_animal(client, headers, pen_id, today - timedelta(days=400))
    overdue = _create_animal(client, headers, pen_id, today - timedelta(days=450))
    farm_id = _farm_id(farm_name)

    _seed_pregnant_mating(farm_id, upcoming["ear_tag"], today + timedelta(days=10))
    _seed_pregnant_mating(farm_id, overdue["ear_tag"], today - timedelta(days=5))

    # 另一个农场的数据不能被本场按需生成带出来
    register_farm(client, "旁观牛场", "alert_other_owner")
    other_farm_id = _farm_id("旁观牛场")
    _seed_pregnant_mating(other_farm_id, "29999", today + timedelta(days=3))

    params = {"alert_type": "临产", "species": SPECIES, "pageSize": 100}
    r = client.get("/api/v1/breeding/alert/list", params=params, headers=headers)
    body = r.json()
    assert body["code"] == 200, body
    data = body["data"]
    assert data["total"] == 2, data
    contents = {a["animal_tag"]: a["alert_content"] for a in data["list"]}
    assert "剩余 10 天" in contents[upcoming["ear_tag"]]
    assert "已逾期 5 天" in contents[overdue["ear_tag"]]
    assert all(a["alert_type"] == "临产" for a in data["list"])

    with TestingSessionLocal() as db:
        assert db.query(BreedingAlert).filter(
            BreedingAlert.farm_id == farm_id, BreedingAlert.alert_type == "临产"
        ).count() == 2
        # 其它农场要等它自己打开页面时才生成
        assert db.query(BreedingAlert).filter(
            BreedingAlert.farm_id == other_farm_id
        ).count() == 0

    # 重复调用：不产生重复数据
    r = client.get("/api/v1/breeding/alert/list", params=params, headers=headers)
    assert r.json()["data"]["total"] == 2
    with TestingSessionLocal() as db:
        assert db.query(BreedingAlert).filter(
            BreedingAlert.farm_id == farm_id, BreedingAlert.alert_type == "临产"
        ).count() == 2


def test_alert_list_still_works_when_generation_fails(client, monkeypatch):
    """按需生成异常只记日志并回滚，不能影响预警列表查询"""
    headers = register_farm(client, "预警异常牛场", "alert_fail_owner")

    def boom(db, farm_id):
        raise RuntimeError("模拟预警生成失败")

    monkeypatch.setattr(breeding_service, "ensure_alerts", boom)

    r = client.get("/api/v1/breeding/alert/list", params={"pageSize": 100}, headers=headers)
    body = r.json()
    assert body["code"] == 200, body
    assert body["data"]["total"] == 0
    assert body["data"]["list"] == []


def test_birth_alert_pushes_message_once_and_is_idempotent(client):
    """新建临产预警时给场主推 1 条站内消息；重复打开列表不重复推送"""
    farm_name = "临产消息牛场"
    headers = register_farm(client, farm_name, "alert_msg_owner")
    today = date.today()
    pen_id = _create_pen(client, headers)
    female = _create_animal(client, headers, pen_id, today - timedelta(days=420))
    farm_id = _farm_id(farm_name)
    mating_id = _seed_pregnant_mating(
        farm_id, female["ear_tag"], today + timedelta(days=10)
    )

    params = {"alert_type": "临产", "pageSize": 100}
    r = client.get("/api/v1/breeding/alert/list", params=params, headers=headers)
    assert r.json()["data"]["total"] == 1, r.json()

    with TestingSessionLocal() as db:
        owner = db.query(User).filter(User.username == "alert_msg_owner").one()
        alert = db.query(BreedingAlert).filter(
            BreedingAlert.farm_id == farm_id, BreedingAlert.alert_type == "临产"
        ).one()
        messages = db.query(SysMessage).filter(
            SysMessage.farm_id == farm_id, SysMessage.receiver_user_id == owner.id
        ).all()
        assert len(messages) == 1, messages
        msg = messages[0]
        assert msg.title == f"临产预警：耳标 {female['ear_tag']}"
        assert "剩余 10 天" in msg.content
        assert msg.related_module == "breeding"
        assert msg.related_id == alert.id
        assert msg.message_type == "系统提醒"
        assert msg.is_read == 0
        alert_id = alert.id
        alert_related_id = alert.related_id

    # 场主可通过站内消息接口看到这条提醒
    r = client.get("/api/v1/system/message/list", params={"pageSize": 100}, headers=headers)
    assert r.json()["data"]["total"] == 1, r.json()
    assert r.json()["data"]["list"][0]["related_id"] == alert_id

    # 重复打开页面：不新增预警、也不新增消息
    r = client.get("/api/v1/breeding/alert/list", params=params, headers=headers)
    assert r.json()["data"]["total"] == 1
    with TestingSessionLocal() as db:
        assert db.query(BreedingAlert).count() == 1
        assert db.query(SysMessage).count() == 1

    # 配种记录 ID 用于后续排查，确保这条预警确实关联到该记录
    assert alert_related_id == mating_id


def test_alert_rules_for_pregnancy_check_and_no_heat(client):
    """孕检满 60 天提醒；产犊满 60 天且无后续通过配种时提醒未发情"""
    farm_name = "预警规则牛场"
    headers = register_farm(client, farm_name, "alert_rule_owner")
    today = date.today()
    pen_id = _create_pen(client, headers)

    female_check = _create_animal(client, headers, pen_id, today - timedelta(days=500))
    female_heat = _create_animal(client, headers, pen_id, today - timedelta(days=500))
    female_with_mating = _create_animal(client, headers, pen_id, today - timedelta(days=500))
    farm_id = _farm_id(farm_name)

    # 待孕检：配种日期刚好满 60 天 → 孕检预警
    _seed_pending_check_mating(farm_id, female_check["ear_tag"], today - timedelta(days=60))
    # 产犊满 60 天且之后没有通过审核的配种 → 未发情预警
    _seed_birth(farm_id, female_heat["ear_tag"], today - timedelta(days=60))
    # 产犊满 60 天但已有通过审核的配种 → 不产生未发情预警
    _seed_birth(farm_id, female_with_mating["ear_tag"], today - timedelta(days=60))
    _seed_pending_check_mating(
        farm_id, female_with_mating["ear_tag"], today - timedelta(days=10)
    )

    r = client.get("/api/v1/breeding/alert/list", params={"pageSize": 100}, headers=headers)
    body = r.json()
    assert body["code"] == 200, body
    data = body["data"]
    assert data["total"] == 2, data
    keys = {(a["animal_tag"], a["alert_type"]) for a in data["list"]}
    assert (female_check["ear_tag"], "孕检") in keys
    assert (female_heat["ear_tag"], "未发情") in keys
    assert all(tag != female_with_mating["ear_tag"] for tag, _ in keys)

    # 这三类提醒不推送临产站内消息
    with TestingSessionLocal() as db:
        assert db.query(SysMessage).count() == 0


def test_scheduler_scans_all_active_farms(client, monkeypatch):
    """每日定时任务逐场生成预警；已删除的养殖场跳过"""
    today = date.today()
    register_farm(client, "调度牛场一", "sched_owner1")
    register_farm(client, "调度牛场二", "sched_owner2")
    register_farm(client, "调度已删除牛场", "sched_owner3")

    farm1_id = _farm_id("调度牛场一")
    farm2_id = _farm_id("调度牛场二")
    deleted_farm_id = _farm_id("调度已删除牛场")

    _seed_pregnant_mating(farm1_id, "10101", today + timedelta(days=10))
    _seed_pregnant_mating(farm2_id, "10201", today + timedelta(days=10))
    _seed_pregnant_mating(deleted_farm_id, "10301", today + timedelta(days=10))
    with TestingSessionLocal() as db:
        db.query(Farm).filter(Farm.id == deleted_farm_id).update({"deleted": True})
        db.commit()

    # 定时任务使用模块级 SessionLocal，测试里替换为 SQLite 内存库会话工厂
    monkeypatch.setattr(scheduler_module, "SessionLocal", TestingSessionLocal)
    scheduler_module.scan_breeding_alerts()

    with TestingSessionLocal() as db:
        assert db.query(BreedingAlert).filter(
            BreedingAlert.farm_id == farm1_id, BreedingAlert.alert_type == "临产"
        ).count() == 1
        assert db.query(BreedingAlert).filter(
            BreedingAlert.farm_id == farm2_id, BreedingAlert.alert_type == "临产"
        ).count() == 1
        assert db.query(BreedingAlert).filter(
            BreedingAlert.farm_id == deleted_farm_id
        ).count() == 0
        # 两个活跃场的场主各收到一条临产消息
        assert db.query(SysMessage).count() == 2
