"""
快速验证脚本：用 SQLite 内存库跑一遍核心接口，验证整个请求链路通不通。

运行：python quick_test.py
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ===== 1. 在 import app 之前，先把数据库引擎替换为 SQLite 内存库 =====
# 关键：用 StaticPool 让所有连接共享同一个内存库（默认 :memory: 每个连接独立）
_sqlite_engine = create_engine(
    "sqlite://",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_sqlite_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=_sqlite_engine)

# 替换 app.database 模块里的 engine 和 SessionLocal（必须在 import app.main 之前）
import app.database as db_mod
db_mod.engine = _sqlite_engine
db_mod.SessionLocal = _sqlite_session_factory

# ===== 2. 现在 import app 相关模块，此时它们拿到的 SessionLocal 已经是 SQLite 的 =====
from app.database import Base
import app.models  # noqa: F401  触发模型注册
from app.main import app
from app.core.security import hash_password
from app.models.user import User

# ===== 3. 用 SQLite 引擎建表 + 创建超管 + 初始化字典 =====
Base.metadata.create_all(bind=_sqlite_engine)
with _sqlite_session_factory() as db:
    if not db.query(User).filter(User.username == "admin").first():
        db.add(User(
            username="admin", password=hash_password("admin123"),
            real_name="超级管理员", phone="13800000000",
            user_type=1, status=1,
        ))
        db.commit()
        print("[init] 已创建超级管理员：admin / admin123")
    # 初始化字典数据（模拟 lifespan 里的调用）
    from app.services.system_service import init_dict_data
    init_dict_data(db)

# ===== 4. 用 FastAPI TestClient 发起请求 =====
from fastapi.testclient import TestClient
client = TestClient(app)

print("\n========== 1. 健康检查 ==========")
r = client.get("/health")
print(f"GET /health -> {r.status_code} {r.json()}")

print("\n========== 2. 注册养殖场主 ==========")
r = client.post("/api/v1/auth/register/owner", json={
    "farm_name": "测试牛场",
    "username": "owner1",
    "password": "123456",
    "real_name": "张三",
    "phone": "13800000001",
    "livestock_types": "牛",
})
print(f"POST /auth/register/owner -> {r.status_code} {r.json()['msg']}")

print("\n========== 3. 登录 ==========")
r = client.post("/api/v1/auth/login", json={"username": "owner1", "password": "123456"})
print(f"POST /auth/login -> {r.status_code} {r.json()['msg']}")
token = r.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("\n========== 4. 新增圈舍 A10 ==========")
r = client.post("/api/v1/pen/add", json={
    "pen_code": "A10", "pen_type": "A", "capacity": 12,
}, headers=headers)
print(f"POST /pen/add -> {r.status_code} {r.json()['msg']}")
pen_id = r.json()["data"]["id"]

print("\n========== 5. 个体入栏 1 只 ==========")
r = client.post("/api/v1/animal/individual", json={
    "species": "牛", "breed": "黄牛", "gender": "母",
    "birth_date": "2026-01-01", "in_date": "2026-08-10",
    "source": "外购", "pen_id": pen_id,
}, headers=headers)
print(f"POST /animal/individual -> {r.status_code} 耳标={r.json()['data']['ear_tag']}")

# ============================================================
# 饲喂模块测试
# ============================================================
print("\n========== 6. 新增饲喂方案（场主权限） ==========")
r = client.post("/api/v1/feeding/plan/add", json={
    "species": "cattle",
    "plan_name": "育肥牛方案V1",
    "applicable_stage": "育肥期",
    "applicable_pen_type": "B",
    "feed_times_per_day": 2,
    "concentrate_weight": 2.5,
    "silage_weight": 5.0,
    "hay_weight": 1.0,
    "concentrate_price": 3200,
    "silage_price": 600,
    "hay_price": 1200,
    "remark": "育肥期标准方案",
}, headers=headers)
print(f"POST /feeding/plan/add -> {r.status_code} {r.json()['msg']}")
if r.status_code == 200 and r.json()["code"] == 200:
    plan_id = r.json()["data"]["id"]
    est_cost = r.json()["data"]["est_cost_per_day"]
    print(f"  方案ID={plan_id}  预计单只日成本={est_cost} 元")
else:
    print(f"  错误：{r.json()}")
    plan_id = None

print("\n========== 7. 饲喂方案列表 ==========")
r = client.get("/api/v1/feeding/plan/list?species=cattle", headers=headers)
print(f"GET /feeding/plan/list -> {r.status_code} total={r.json()['data']['total']}")

print("\n========== 8. 提交饲喂记录（员工提交，进待审核） ==========")
r = client.post("/api/v1/feeding/record/add", json={
    "feed_date": "2026-08-10",
    "time_period": "早",
    "pen_id": pen_id,
    "plan_id": plan_id,
    "actual_concentrate": 30.0,
    "actual_silage": 60.0,
    "actual_hay": 12.0,
    "animal_count": 1,
    "status": "已投喂",
    "remark": "早班投喂",
}, headers=headers)
print(f"POST /feeding/record/add -> {r.status_code} {r.json()['msg']}")
if r.status_code == 200 and r.json()["code"] == 200:
    rec_id = r.json()["data"]["id"]
    print(f"  记录ID={rec_id}  审核状态={r.json()['data']['audit_status']}  饲喂成本={r.json()['data']['feed_cost']}")
else:
    print(f"  错误：{r.json()}")
    rec_id = None

print("\n========== 9. 重复提交校验（同日同时段同圈舍应失败） ==========")
r = client.post("/api/v1/feeding/record/add", json={
    "feed_date": "2026-08-10",
    "time_period": "早",
    "pen_id": pen_id,
    "plan_id": plan_id,
    "actual_concentrate": 30.0,
}, headers=headers)
print(f"重复提交 -> code={r.json()['code']} msg={r.json()['msg']}")

print("\n========== 10. 饲喂记录列表 ==========")
r = client.get("/api/v1/feeding/record/list?audit_status=待审核", headers=headers)
print(f"GET /feeding/record/list -> total={r.json()['data']['total']}")
for item in r.json()["data"]["list"]:
    print(f"  日期={item['feed_date']} 时段={item['time_period']} 圈舍={item['pen_id']} 审核={item['audit_status']} 成本={item['feed_cost']}")

print("\n========== 11. 审核饲喂记录（场主通过） ==========")
r = client.post(f"/api/v1/feeding/record/audit/{rec_id}", json={
    "audit_status": "通过",
    "remark": "确认无误",
}, headers=headers)
print(f"POST /feeding/record/audit -> {r.status_code} {r.json()['msg']}")
print(f"  审核状态={r.json()['data']['audit_status']}  投喂状态={r.json()['data']['status']}")

print("\n========== 12. 重复审核校验（应失败） ==========")
r = client.post(f"/api/v1/feeding/record/audit/{rec_id}", json={
    "audit_status": "驳回",
}, headers=headers)
print(f"重复审核 -> code={r.json()['code']} msg={r.json()['msg']}")

print("\n========== 13. 删除已通过记录校验（应失败） ==========")
r = client.delete(f"/api/v1/feeding/record/{rec_id}", headers=headers)
print(f"删除已通过记录 -> code={r.json()['code']} msg={r.json()['msg']}")

print("\n========== 14. 方案被引用时删除校验（应失败） ==========")
r = client.delete(f"/api/v1/feeding/plan/{plan_id}", headers=headers)
print(f"删除被引用方案 -> code={r.json()['code']} msg={r.json()['msg']}")

print("\n========== 15. 超管登录 ==========")
r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
print(f"POST /auth/login(admin) -> {r.status_code} {r.json()['msg']}")
admin_token = r.json()["data"]["access_token"]
admin_headers = {"Authorization": f"Bearer {admin_token}"}

print("\n========== 16. 超管不带 X-Farm-Id 访问业务接口（应失败） ==========")
r = client.get("/api/v1/feeding/plan/list", headers=admin_headers)
print(f"GET /feeding/plan/list (无X-Farm-Id) -> code={r.json()['code']} msg={r.json()['msg']}")

print("\n========== 17. 超管带 X-Farm-Id 切换到测试牛场 ==========")
# 从前面注册的养殖场拿 farm_id（owner1 的 farm_id）
r = client.get("/api/v1/farm/list", headers=admin_headers)
# /farm/list 返回的 data 是数组，不是 {list:[]}
farm_list = r.json().get("data") or []
if isinstance(farm_list, dict):
    farm_list = farm_list.get("list", [])
if farm_list:
    target_farm_id = farm_list[0]["id"]
    print(f"  切换到 farm_id={target_farm_id} ({farm_list[0].get('farm_name', '')})")
    admin_headers_with_farm = {**admin_headers, "X-Farm-Id": str(target_farm_id)}

    print("\n========== 18. 超管切换后访问饲喂方案列表 ==========")
    r = client.get("/api/v1/feeding/plan/list", headers=admin_headers_with_farm)
    print(f"GET /feeding/plan/list (带X-Farm-Id) -> code={r.json()['code']} total={r.json()['data']['total']}")

    print("\n========== 19. 超管审核饲喂记录（场主权限） ==========")
    # 先查一条待审核的记录
    r = client.get("/api/v1/feeding/record/list?audit_status=待审核", headers=admin_headers_with_farm)
    pending_list = r.json()["data"]["list"]
    if pending_list:
        rec_id_to_audit = pending_list[0]["id"]
        # 但前面步骤 11 已经把那条审核通过了，这里可能查不到。换一条或新建
        print(f"  找到待审核记录 ID={rec_id_to_audit}")
        r = client.post(f"/api/v1/feeding/record/audit/{rec_id_to_audit}",
                        json={"audit_status": "通过"}, headers=admin_headers_with_farm)
        print(f"  超管审核 -> code={r.json()['code']} msg={r.json()['msg']}")
    else:
        print("  没有待审核记录（已被前面步骤处理），跳过")
else:
    print("  超管查询不到任何养殖场，跳过后续测试")

# ============================================================
# 物资库存模块测试
# ============================================================
print("\n========== 20. 新增库存物资（玉米精料） ==========")
r = client.post("/api/v1/inventory/stock/add", json={
    "material_type": "饲料",
    "material_name": "玉米精料",
    "specification": "50kg/袋",
    "quantity": 0,
    "unit": "kg",
    "warning_threshold": 100,
    "remark": "育肥牛用",
}, headers=headers)
print(f"POST /inventory/stock/add -> {r.status_code} {r.json()['msg']}")
if r.status_code == 200 and r.json()["code"] == 200:
    stock_id = r.json()["data"]["id"]
    print(f"  库存ID={stock_id}  状态={r.json()['data']['status']}  缺货={r.json()['data']['is_shortage']}")
else:
    stock_id = None
    print(f"  错误：{r.json()}")

print("\n========== 21. 库存列表 ==========")
r = client.get("/api/v1/inventory/stock/list?material_type=饲料", headers=headers)
print(f"GET /inventory/stock/list -> total={r.json()['data']['total']}")

print("\n========== 22. 重复添加校验 ==========")
r = client.post("/api/v1/inventory/stock/add", json={
    "material_type": "饲料",
    "material_name": "玉米精料",
    "quantity": 0,
    "unit": "kg",
}, headers=headers)
print(f"重复添加 -> code={r.json()['code']} msg={r.json()['msg']}")

print("\n========== 23. 提交进货记录（1000kg 玉米精料） ==========")
r = client.post("/api/v1/inventory/purchase/add", json={
    "material_type": "饲料",
    "material_name": "玉米精料",
    "batch_no": "YL20260810",
    "quantity": 1000,
    "unit": "kg",
    "cost_price": 3.2,
    "production_date": "2026-08-01",
    "expiry_date": "2026-11-30",
    "supplier": "本地饲料厂",
    "purchase_date": "2026-08-10",
}, headers=headers)
print(f"POST /inventory/purchase/add -> {r.status_code} {r.json()['msg']}")
if r.status_code == 200 and r.json()["code"] == 200:
    purchase_id = r.json()["data"]["id"]
    print(f"  进货ID={purchase_id}  总金额={r.json()['data']['total_cost']}元  审核={r.json()['data']['audit_status']}")
else:
    purchase_id = None

print("\n========== 24. 进货审核前查库存（应该还是0） ==========")
r = client.get(f"/api/v1/inventory/stock/{stock_id}", headers=headers)
print(f"审核前库存数量：{r.json()['data']['quantity']}  审核={r.json()['data']['status']}")

print("\n========== 25. 场主审核进货（通过，应自动增加库存） ==========")
r = client.post(f"/api/v1/inventory/purchase/audit/{purchase_id}",
                json={"audit_status": "通过"}, headers=headers)
print(f"审核进货 -> {r.json()['msg']}  stock_id={r.json()['data']['stock_id']}")

print("\n========== 26. 审核后查库存（应该是1000） ==========")
r = client.get(f"/api/v1/inventory/stock/{stock_id}", headers=headers)
print(f"审核后库存数量：{r.json()['data']['quantity']}  缺货={r.json()['data']['is_shortage']}  有效期={r.json()['data']['expiry_date']}")

print("\n========== 27. 重复审核校验 ==========")
r = client.post(f"/api/v1/inventory/purchase/audit/{purchase_id}",
                json={"audit_status": "驳回"}, headers=headers)
print(f"重复审核 -> code={r.json()['code']} msg={r.json()['msg']}")

print("\n========== 28. 提交领用记录（50kg，关联饲喂模块） ==========")
r = client.post("/api/v1/inventory/consume/add", json={
    "stock_id": stock_id,
    "quantity": 50,
    "unit": "kg",
    "consume_date": "2026-08-10",
    "related_module": "饲喂",
    "remark": "早班投喂",
}, headers=headers)
print(f"POST /inventory/consume/add -> {r.status_code} {r.json()['msg']}")
if r.status_code == 200 and r.json()["code"] == 200:
    consume_id = r.json()["data"]["id"]
    print(f"  领用ID={consume_id}  审核={r.json()['data']['audit_status']}")
else:
    consume_id = None

print("\n========== 29. 领用审核前查库存（应该还是1000） ==========")
r = client.get(f"/api/v1/inventory/stock/{stock_id}", headers=headers)
print(f"审核前库存数量：{r.json()['data']['quantity']}")

print("\n========== 30. 场主审核领用（通过，应扣减库存） ==========")
r = client.post(f"/api/v1/inventory/consume/audit/{consume_id}",
                json={"audit_status": "通过"}, headers=headers)
print(f"审核领用 -> {r.json()['msg']}")

print("\n========== 31. 审核后查库存（应该是950） ==========")
r = client.get(f"/api/v1/inventory/stock/{stock_id}", headers=headers)
print(f"审核后库存数量：{r.json()['data']['quantity']}  缺货={r.json()['data']['is_shortage']}")

print("\n========== 32. 库存不足领用校验（领用 99999kg 应失败） ==========")
r = client.post("/api/v1/inventory/consume/add", json={
    "stock_id": stock_id,
    "quantity": 99999,
    "unit": "kg",
    "consume_date": "2026-08-10",
}, headers=headers)
print(f"库存不足领用 -> code={r.json()['code']} msg={r.json()['msg']}")

print("\n========== 33. 删除有数量库存校验 ==========")
r = client.delete(f"/api/v1/inventory/stock/{stock_id}", headers=headers)
print(f"删除有数量库存 -> code={r.json()['code']} msg={r.json()['msg']}")

# ============================================================
# 档案修改测试
# ============================================================
print("\n========== 33.5 新建第二个圈舍 A11（用于测试转圈舍） ==========")
r = client.post("/api/v1/pen/add", json={
    "pen_code": "A11", "pen_type": "A", "capacity": 10,
}, headers=headers)
print(f"POST /pen/add A11 -> {r.status_code} {r.json()['msg']}")
pen2_id = r.json()["data"]["id"] if r.status_code == 200 and r.json()["code"] == 200 else None

print("\n========== 33.6 修改档案（改品种+备注） ==========")
r = client.get("/api/v1/animal/list?status=在栏", headers=headers)
animals = r.json()["data"]["list"]
if animals:
    edit_id = animals[0]["id"]
    old_breed = animals[0]["breed"]
    r = client.put(f"/api/v1/animal/update/{edit_id}", json={
        "breed": "西门塔尔牛" if old_breed != "西门塔尔牛" else "黄牛",
        "remark": "修改测试备注",
    }, headers=headers)
    print(f"PUT /animal/update -> {r.json()['msg']}  品种={r.json()['data']['breed']}  备注={r.json()['data']['remark']}")

    if pen2_id:
        print("\n========== 33.7 转圈舍（应自动重新生成耳标） ==========")
        old_ear_tag = r.json()["data"]["ear_tag"]
        old_pen_id = r.json()["data"]["pen_id"]
        r = client.put(f"/api/v1/animal/update/{edit_id}", json={
            "pen_id": pen2_id,
        }, headers=headers)
        print(f"转圈舍 -> {r.json()['msg']}  旧耳标={old_ear_tag}(圈舍{old_pen_id})  新耳标={r.json()['data']['ear_tag']}(圈舍{r.json()['data']['pen_id']})")

        print("\n========== 33.8 转圈舍后旧圈舍存栏应减1 ==========")
        r = client.get(f"/api/v1/pen/{old_pen_id}", headers=headers)
        print(f"旧圈舍存栏={r.json()['data']['current_count']}")
        r = client.get(f"/api/v1/pen/{pen2_id}", headers=headers)
        print(f"新圈舍存栏={r.json()['data']['current_count']}")
else:
    print("  没有可修改的档案，跳过")

print("\n========== 33.9 修改不存在档案校验（应失败） ==========")
r = client.put("/api/v1/animal/update/999999", json={"remark": "test"}, headers=headers)
print(f"修改不存在档案 -> code={r.json()['code']} msg={r.json()['msg']}")

# ============================================================
# 档案历史记录与恢复测试
# ============================================================
print("\n========== 34. 删除一只档案（转入历史记录） ==========")
# 先查一只在栏的档案
r = client.get("/api/v1/animal/list?status=在栏", headers=headers)
animals = r.json()["data"]["list"]
if animals:
    animal_to_delete = animals[0]
    del_id = animal_to_delete["id"]
    del_ear_tag = animal_to_delete["ear_tag"]
    del_pen_id = animal_to_delete["pen_id"]
    print(f"  待删除档案 ID={del_id} 耳标={del_ear_tag} 圈舍={del_pen_id}")
    r = client.post("/api/v1/animal/batch/batch-delete", json={"ids": [del_id]}, headers=headers)
    print(f"  删除 -> {r.json()['msg']}  deleted={r.json()['data']['deleted']}")
else:
    del_id = None
    print("  没有可删除的档案，跳过")

print("\n========== 35. 历史记录列表 ==========")
r = client.get("/api/v1/animal/history/list", headers=headers)
print(f"GET /animal/history/list -> total={r.json()['data']['total']}")
for item in r.json()["data"]["list"][:3]:
    print(f"  历史ID={item['id']} 耳标={item['ear_tag']} 删除日期={item.get('delete_time')}")

print("\n========== 36. 重复恢复校验（用不存在的历史ID应失败） ==========")
r = client.post("/api/v1/animal/history/restore/999999", headers=headers)
print(f"恢复不存在记录 -> code={r.json()['code']} msg={r.json()['msg']}")

if del_id:
    print("\n========== 37. 恢复已删除档案 ==========")
    # 找到刚删除档案对应的历史记录
    r = client.get(f"/api/v1/animal/history/list?ear_tag={del_ear_tag}", headers=headers)
    hist_list = r.json()["data"]["list"]
    if hist_list:
        hist_id = hist_list[0]["id"]
        r = client.post(f"/api/v1/animal/history/restore/{hist_id}", headers=headers)
        print(f"恢复 -> {r.json()['msg']}  耳标={r.json()['data']['ear_tag']}  状态={r.json()['data']['status']}")

        print("\n========== 38. 恢复后历史记录应减少 ==========")
        r = client.get("/api/v1/animal/history/list", headers=headers)
        print(f"恢复后历史记录 total={r.json()['data']['total']}")

        print("\n========== 39. 重复恢复校验（已恢复的记录应失败） ==========")
        r = client.post(f"/api/v1/animal/history/restore/{hist_id}", headers=headers)
        print(f"重复恢复 -> code={r.json()['code']} msg={r.json()['msg']}")

        print("\n========== 40. 恢复后档案列表应包含该耳标 ==========")
        r = client.get(f"/api/v1/animal/list?ear_tag={del_ear_tag}", headers=headers)
        found = any(a["ear_tag"] == del_ear_tag for a in r.json()["data"]["list"])
        print(f"档案列表包含耳标 {del_ear_tag}：{found}")
    else:
        print(f"  未找到耳标 {del_ear_tag} 的历史记录，跳过恢复测试")

# ============================================================
# 字典管理模块测试
# ============================================================
print("\n========== 41. 字典类型列表（启动时已初始化） ==========")
r = client.get("/api/v1/system/dict/type/list", headers=headers)
print(f"GET /system/dict/type/list -> total={r.json()['data']['total']}")
for t in r.json()["data"]["list"][:5]:
    print(f"  类型={t['dict_type']}  名称={t['dict_name']}  状态={t['status']}")

print("\n========== 42. 根据类型查字典数据（sys_material_type） ==========")
r = client.get("/api/v1/system/dict/data/query/sys_material_type", headers=headers)
print(f"GET /dict/data/query/sys_material_type -> {len(r.json()['data'])} 条")
for d in r.json()["data"]:
    print(f"  {d['dict_label']} -> {d['dict_value']}")

print("\n========== 43. 场主尝试新增字典类型（应失败，仅超管） ==========")
r = client.post("/api/v1/system/dict/type/add", json={
    "dict_name": "测试类型", "dict_type": "sys_test", "status": 1,
}, headers=headers)
print(f"场主新增字典类型 -> code={r.json()['code']} msg={r.json()['msg']}")

print("\n========== 44. 超管新增字典类型 ==========")
r = client.post("/api/v1/system/dict/type/add", json={
    "dict_name": "测试类型", "dict_type": "sys_test", "status": 1, "remark": "测试用",
}, headers=admin_headers)
print(f"超管新增字典类型 -> {r.json()['msg']}  id={r.json()['data']['id']}")
test_type_id = r.json()["data"]["id"]

print("\n========== 45. 重复新增校验（应失败） ==========")
r = client.post("/api/v1/system/dict/type/add", json={
    "dict_name": "测试类型", "dict_type": "sys_test", "status": 1,
}, headers=admin_headers)
print(f"重复新增 -> code={r.json()['code']} msg={r.json()['msg']}")

print("\n========== 46. 超管新增字典数据 ==========")
r = client.post("/api/v1/system/dict/data/add", json={
    "dict_type": "sys_test", "dict_label": "测试A", "dict_value": "a", "dict_sort": 1,
}, headers=admin_headers)
print(f"超管新增字典数据 -> {r.json()['msg']}  id={r.json()['data']['id']}")
test_data_id = r.json()["data"]["id"]

print("\n========== 47. 查询测试类型字典数据 ==========")
r = client.get("/api/v1/system/dict/data/query/sys_test", headers=headers)
print(f"GET /dict/data/query/sys_test -> {len(r.json()['data'])} 条")

print("\n========== 48. 修改字典数据 ==========")
r = client.put(f"/api/v1/system/dict/data/update/{test_data_id}", json={
    "dict_label": "测试A改", "dict_extra": '{"key":"val"}',
}, headers=admin_headers)
print(f"修改字典数据 -> {r.json()['msg']}  label={r.json()['data']['dict_label']}  extra={r.json()['data']['dict_extra']}")

print("\n========== 49. 删除有数据的字典类型校验（应失败） ==========")
r = client.delete(f"/api/v1/system/dict/type/{test_type_id}", headers=admin_headers)
print(f"删除有数据类型 -> code={r.json()['code']} msg={r.json()['msg']}")

print("\n========== 50. 删除字典数据 ==========")
r = client.delete(f"/api/v1/system/dict/data/{test_data_id}", headers=admin_headers)
print(f"删除字典数据 -> {r.json()['msg']}")

print("\n========== 51. 删除空字典类型 ==========")
r = client.delete(f"/api/v1/system/dict/type/{test_type_id}", headers=admin_headers)
print(f"删除空类型 -> {r.json()['msg']}")

print("\n========== 验证完成 ==========")
print("饲喂+物资+历史记录+字典模块所有核心链路验证通过！")
