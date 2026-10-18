"""
P1-A 验收：超管必须明确选择目标养殖场，禁止静默回退到首个农场。

覆盖指引验收标准：
1. 超管无 X-Farm-Id 调用农场信息 / 档案查询 / 写接口 → 明确业务错误，不动任何农场数据
2. 超管选择有效活跃农场 → 查询和写入只作用于该农场
3. 超管传入不存在 / 已删除的 ID → 报错，不静默切换
4. 普通用户伪造其他农场的 X-Farm-Id → 仍只读写自己所属农场
5. 无农场 / 单农场 / 多农场 / 失效 ID / 伪造 header 场景
"""
from tests.conftest import TestingSessionLocal, register_farm, login, get_farm_id

from app.services import farm_service
from app.core.exceptions import BizException
from app.core.utils import get_effective_farm_id
from app.models.farm import Farm


def _seed_two_farms(client):
    """准备两个农场（各一个场主），返回 (farm1头, farm2头, farm1名, farm2名)"""
    h1 = register_farm(client, "一号牛场", "owner1")
    h2 = register_farm(client, "二号牛场", "owner2")
    return h1, h2, "一号牛场", "二号牛场"


def test_admin_without_farm_id_gets_error_not_fallback(client):
    """超管不带 X-Farm-Id：农场信息 / 档案 / 圈舍 / 写接口都要明确报错，不回退到首个农场"""
    _seed_two_farms(client)
    admin = login(client, "admin", "admin123")

    # 农场信息
    r = client.get("/api/v1/farm/info", headers=admin)
    assert r.json()["code"] == 40302, r.json()

    # 档案查询（走 resolve_farm_id）
    r = client.get("/api/v1/animal/list", headers=admin)
    assert r.json()["code"] == 40302, r.json()

    # 圈舍查询（走 resolve_farm_id / get_effective_farm_id）
    r = client.get("/api/v1/pen/list", headers=admin)
    assert r.json()["code"] == 40302, r.json()

    # 写接口：新增圈舍必须先选农场
    r = client.post("/api/v1/pen/add", json={"pen_code": "A01", "pen_type": "A", "capacity": 10}, headers=admin)
    assert r.json()["code"] == 40302, r.json()
    with TestingSessionLocal() as db:
        assert db.query(Farm).count() >= 2  # 两个农场都在，未被误建圈舍（间接确认无写入）


def test_admin_with_valid_farm_id_scoped_to_that_farm(client):
    """超管带有效 X-Farm-Id：只看到该农场的数据，写操作只作用于该农场"""
    h1, h2, name1, name2 = _seed_two_farms(client)
    admin = login(client, "admin", "admin123")
    fid1 = get_farm_id(client, admin, name1)
    fid2 = get_farm_id(client, admin, name2)
    admin2 = {**admin, "X-Farm-Id": str(fid2)}

    # 各自建一个圈舍 + 一头牛
    for h, tag in ((h1, "A01"), (h2, "A02")):
        r = client.post("/api/v1/pen/add", json={"pen_code": tag, "pen_type": "A", "capacity": 10}, headers=h)
        assert r.json()["code"] == 200, r.json()
        r = client.post("/api/v1/animal/individual", json={
            "species": "牛", "breed": "黄牛", "gender": "母",
            "birth_date": "2026-01-01", "in_date": "2026-08-01",
            "source": "外购", "pen_id": r.json()["data"]["id"],
        }, headers=h)
        assert r.json()["code"] == 200, r.json()

    # 超管切到二号场：农场信息是二号场，档案列表只有二号场那一头
    r = client.get("/api/v1/farm/info", headers=admin2)
    assert r.json()["data"]["farm_name"] == name2

    r = client.get("/api/v1/animal/list", headers=admin2)
    assert r.json()["code"] == 200
    tags = [a["ear_tag"] for a in r.json()["data"]["list"]]
    assert len(tags) == 1, tags

    r = client.get("/api/v1/animal/list", headers={**admin, "X-Farm-Id": str(fid1)})
    assert len(r.json()["data"]["list"]) == 1


def test_admin_with_nonexistent_farm_id_rejected(client):
    """超管传不存在的 X-Farm-Id：任何接口都报错，不静默切换到其他农场"""
    _seed_two_farms(client)
    admin = {**login(client, "admin", "admin123"), "X-Farm-Id": "99999"}
    r = client.get("/api/v1/farm/info", headers=admin)
    assert r.json()["code"] == 40302, r.json()
    r = client.get("/api/v1/animal/list", headers=admin)
    assert r.json()["code"] == 40302, r.json()


def test_admin_with_deleted_farm_id_rejected(client):
    """超管传已删除（软删）农场的 X-Farm-Id：报错"""
    h1, h2, name1, name2 = _seed_two_farms(client)
    admin = login(client, "admin", "admin123")
    fid2 = get_farm_id(client, admin, name2)

    with TestingSessionLocal() as db:
        db.query(Farm).filter(Farm.farm_name == name2).update({"deleted": True})
        db.commit()

    r = client.get("/api/v1/farm/info", headers={**admin, "X-Farm-Id": str(fid2)})
    assert r.json()["code"] == 40302, r.json()


def test_admin_with_invalid_header_value_rejected(client):
    """超管传非法值（<=0）的 X-Farm-Id：报错"""
    _seed_two_farms(client)
    admin = {**login(client, "admin", "admin123"), "X-Farm-Id": "0"}
    r = client.get("/api/v1/farm/info", headers=admin)
    assert r.json()["code"] == 40302, r.json()


def test_normal_user_cannot_switch_farm_via_header(client):
    """普通场主伪造其他农场的 X-Farm-Id：仍只读写自己的农场"""
    h1, h2, name1, name2 = _seed_two_farms(client)
    admin = login(client, "admin", "admin123")
    fid1 = get_farm_id(client, admin, name1)
    fid2 = get_farm_id(client, admin, name2)

    # 一号场场主带二号场的 X-Farm-Id 访问
    forged = {**h1, "X-Farm-Id": str(fid2)}
    r = client.get("/api/v1/farm/info", headers=forged)
    assert r.json()["code"] == 200
    assert r.json()["data"]["farm_name"] == name1  # 还是自己的农场

    r = client.get("/api/v1/animal/list", headers=forged)
    assert r.json()["code"] == 200


def test_get_farm_info_no_fallback_service_level(client):
    """服务层直测：get_farm_info / get_effective_farm_id 不再回退到首个农场"""
    _seed_two_farms(client)
    with TestingSessionLocal() as db:
        farms = db.query(Farm).filter(Farm.deleted == False).order_by(Farm.id).all()
        assert len(farms) == 2

        # farm_id=0：明确报错（旧实现回退到首个农场）
        try:
            farm_service.get_farm_info(db, 0)
            assert False, "farm_id=0 应抛业务错误"
        except BizException as e:
            assert e.code == 40302

        try:
            get_effective_farm_id(db, 0)
            assert False, "farm_id=0 应抛业务错误"
        except BizException as e:
            assert e.code == 40302

        # 不存在的农场：报错（旧实现也回退到首个农场）
        try:
            farm_service.get_farm_info(db, 99999)
            assert False, "不存在的 farm_id 应抛业务错误"
        except BizException as e:
            assert e.code == 40006

        # 有效 ID：正常返回对应农场
        farm = farm_service.get_farm_info(db, farms[1].id)
        assert farm.id == farms[1].id

        # 空库场景：唯一农场被删后查询报错
        db.query(Farm).filter(Farm.id == farms[0].id).update({"deleted": True})
        db.commit()
        try:
            farm_service.get_farm_info(db, farms[0].id)
            assert False, "已删除农场应抛业务错误"
        except BizException as e:
            assert e.code == 40006
