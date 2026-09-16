"""
阳光牧场测试数据初始化脚本

通过 TestClient 调用真实 API 完成数据初始化：
- 自动 bcrypt 哈希密码
- 自动耳标生成 + 圈舍自动分配
- 自动生长阶段判定
- 自动饲喂成本计算

执行方式：
    cd livestock_server
    python init_sunshine_data.py           # 写入 .env 配置的真实 MySQL 数据库
    python init_sunshine_data.py --sqlite  # 用 SQLite 内存库（仅打印不持久化，CI 用）

数据库会被清空重新初始化（仅 dev 环境用，请勿在生产环境运行）。
"""
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ===== 1. 选择数据库引擎 =====
USE_SQLITE = "--sqlite" in sys.argv

if USE_SQLITE:
    # SQLite 内存库：用于 CI 或快速验证，不持久化
    _engine = create_engine(
        "sqlite://",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    print("[模式] SQLite 内存库（数据不持久化，仅打印验证）")
else:
    # 真实 MySQL：从 .env 读配置，造的数据会持久化
    from app.config import settings
    _engine = create_engine(settings.db_url, echo=False, pool_pre_ping=True)
    print(f"[模式] MySQL 真实数据库：{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

# 替换 app.database 模块里的 engine 和 SessionLocal（必须在 import app.main 之前）
import app.database as db_mod
db_mod.engine = _engine
db_mod.SessionLocal = _session_factory

from app.database import Base
import app.models  # noqa
from app.main import app
from app.core.security import hash_password
from app.models.user import User

# ===== 2. 清空旧数据（保留表结构）=====
if USE_SQLITE:
    Base.metadata.create_all(bind=_engine)
else:
    # MySQL：先建表（如果不存在），再清空数据
    Base.metadata.create_all(bind=_engine)
    print("\n[清空] 清理旧数据...")
    with _engine.connect() as conn:
        # 按外键依赖倒序清空
        for table in ["material_consume", "material_purchase", "material_stock",
                      "feeding_record", "feeding_plan", "animal_archive_history",
                      "animal_archive", "pen_info", "sys_user", "farm_info"]:
            try:
                conn.execute(text(f"DELETE FROM {table}"))
                print(f"  - {table} 已清空")
            except Exception as e:
                print(f"  - {table} 跳过：{e}")
        conn.commit()

# ===== 3. 初始化超管 =====
with _session_factory() as db:
    if not db.query(User).filter(User.username == "admin").first():
        db.add(User(
            username="admin", password=hash_password("admin123"),
            real_name="超级管理员", phone="13800000000",
            user_type=1, status=1,
        ))
        db.commit()
        print("[init] 已创建超级管理员：admin / admin123")
    else:
        print("[init] 超级管理员已存在：admin / admin123")

from fastapi.testclient import TestClient
client = TestClient(app)

print("=" * 70)
print("  阳光牧场 - 测试数据初始化")
print("=" * 70)

# ============================================================
# 1. 注册阳光牧场场主
# ============================================================
print("\n[1/9] 注册阳光牧场场主...")
r = client.post("/api/v1/auth/register/owner", json={
    "farm_name": "阳光牧场",
    "username": "sunshine",
    "password": "123456",
    "real_name": "王阳光",
    "phone": "13900000001",
    "livestock_types": "牛,羊,猪",
})
print(f"  -> {r.json()['msg']}")
owner_token = client.post("/api/v1/auth/login",
    json={"username": "sunshine", "password": "123456"}).json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {owner_token}"}

# 查养殖场 ID
farm_info = client.get("/api/v1/farm/info", headers=headers).json()["data"]
farm_id = farm_info["id"]
print(f"  养殖场ID={farm_id}  名称={farm_info['farm_name']}  种类={farm_info['livestock_types']}")

# ============================================================
# 2. 注册员工（饲喂员 + 兽医）
# ============================================================
print("\n[2/9] 注册员工...")
# 员工注册需要场主 token，通过 farm/employees/add 接口
for emp in [
    {"username": "feeder01", "password": "123456", "real_name": "李饲喂", "phone": "13900000010", "post": "饲喂员"},
    {"username": "feeder02", "password": "123456", "real_name": "张饲喂", "phone": "13900000011", "post": "饲喂员"},
    {"username": "vet01", "password": "123456", "real_name": "陈兽医", "phone": "13900000012", "post": "兽医"},
]:
    r = client.post("/api/v1/farm/employees", json=emp, headers=headers)
    print(f"  -> {emp['username']} ({emp['post']}): {r.json().get('msg', r.json())}")

# 补绑员工岗位角色：本脚本用 TestClient 不触发 lifespan，RBAC 角色由后端启动时创建，
# 创建员工时角色可能尚不存在导致 assign_role_by_post 静默跳过，这里确保每位员工都有关联角色
from app.modules.system.service import assign_role_by_post
from app.models.user import User
_session = _session_factory()
for emp in [
    {"username": "feeder01", "post": "饲喂员"},
    {"username": "feeder02", "post": "饲喂员"},
    {"username": "vet01", "post": "兽医"},
]:
    u = _session.query(User).filter(User.username == emp["username"]).first()
    if u:
        assign_role_by_post(_session, u.id, u.post)
_session.close()
print("  -> 员工岗位角色补绑完成")

# ============================================================
# 3. 创建圈舍（按备注归属畜种：犊牛/育成牛/母牛/种公牛=牛，羔羊/育成羊=羊，育成猪/母猪=猪）
#    耳标 5 位规则：畜种位 + 圈舍编号数字(2位) + 入栏序号(2位)，
#    同畜种内编号数字必须唯一，故各畜种编号数字各自连续：
#    牛 A01/B02/C03/D04、羊 A01/B02、猪 B03/C02（编号只在畜种内唯一，牛A01与羊A01可并存）
# ============================================================
print("\n[3/9] 创建圈舍...")
pens = []
for pen_code, pen_type, capacity, species, remark in [
    ("A01", "A", 12, "牛", "犊牛保育舍"),
    ("A01", "A", 12, "羊", "羔羊保育舍"),
    ("B02", "B", 12, "牛", "育成牛舍"),
    ("B02", "B", 12, "羊", "育成羊舍"),
    ("B03", "B", 12, "猪", "育成猪舍"),
    ("C03", "C", 6, "牛", "母牛繁育舍"),
    ("C02", "C", 6, "猪", "母猪繁育舍"),
    ("D04", "D", 1, "牛", "种公牛舍"),
]:
    r = client.post("/api/v1/pen/add", json={
        "pen_code": pen_code, "pen_type": pen_type,
        "capacity": capacity, "remark": remark, "species": species,
    }, headers=headers)
    if r.status_code == 200 and r.json()["code"] == 200:
        pens.append({"id": r.json()["data"]["id"], "code": pen_code, "type": pen_type, "species": species})
        print(f"  {pen_code} ({pen_type}类/{species}) -> ID={r.json()['data']['id']}  {remark}")
    else:
        print(f"  {pen_code} ({species}) -> {r.json()}")

def pen_id(code, species):
    return next(p["id"] for p in pens if p["code"] == code and p["species"] == species)

pen_a01 = pen_id("A01", "牛")   # 犊牛保育舍
pen_a02 = pen_id("A01", "羊")   # 羔羊保育舍
pen_b01 = pen_id("B02", "牛")   # 育成牛舍
pen_b02 = pen_id("B02", "羊")   # 育成羊舍
pen_b03 = pen_id("B03", "猪")   # 育成猪舍
pen_c01 = pen_id("C03", "牛")   # 母牛繁育舍
pen_c02 = pen_id("C02", "猪")   # 母猪繁育舍
pen_d01 = pen_id("D04", "牛")   # 种公牛舍

# ============================================================
# 4. 个体入栏（牛4 + 羊2 + 猪2）
# ============================================================
print("\n[4/9] 个体入栏...")
animals = [
    # 4 头牛（不同阶段，分别进 A01/B01/C01/D01）
    {"species": "牛", "breed": "西门塔尔牛", "gender": "母", "birth_date": "2026-06-01", "in_date": "2026-08-01", "source": "外购", "pen_id": pen_a01, "remark": "犊牛"},
    {"species": "牛", "breed": "西门塔尔牛", "gender": "母", "birth_date": "2025-12-01", "in_date": "2026-02-01", "source": "外购", "pen_id": pen_b01, "remark": "育成牛"},
    {"species": "牛", "breed": "黄牛", "gender": "母", "birth_date": "2024-01-01", "in_date": "2024-03-01", "source": "外购", "pen_id": pen_c01, "remark": "可繁育母牛"},
    {"species": "牛", "breed": "黄牛", "gender": "公", "birth_date": "2023-06-01", "in_date": "2024-01-01", "source": "自繁", "pen_id": pen_d01, "remark": "种公牛"},
    # 2 只羊
    {"species": "羊", "breed": "小尾寒羊", "gender": "母", "birth_date": "2026-06-15", "in_date": "2026-08-05", "source": "外购", "pen_id": pen_a02, "remark": "羔羊"},
    {"species": "羊", "breed": "杜泊羊", "gender": "母", "birth_date": "2025-10-01", "in_date": "2025-12-01", "source": "外购", "pen_id": pen_b02, "remark": "育成羊"},
    # 2 头猪
    {"species": "猪", "breed": "大白猪", "gender": "母", "birth_date": "2026-06-20", "in_date": "2026-08-05", "source": "外购", "pen_id": pen_b03, "remark": "仔猪转保育"},
    {"species": "猪", "breed": "长白猪", "gender": "母", "birth_date": "2025-11-01", "in_date": "2026-01-01", "source": "外购", "pen_id": pen_c02, "remark": "可繁育母猪"},
]
for a in animals:
    r = client.post("/api/v1/animal/individual", json=a, headers=headers)
    if r.status_code == 200 and r.json()["code"] == 200:
        d = r.json()["data"]
        print(f"  {d['species']}({d['breed']}) 耳标={d['ear_tag']} 圈舍ID={d['pen_id']} 阶段={d['growth_stage']}")
    else:
        print(f"  {a['species']} -> {r.json()}")

# ============================================================
# 5. 批量入栏（4 头育肥牛，自动分配到育成牛舍 B02）
# ============================================================
print("\n[5/9] 批量入栏 4 头育肥牛...")
r = client.post("/api/v1/animal/batch", json={
    "species": "牛", "breed": "安格斯牛", "gender": "公",
    "birth_date": "2025-06-01", "in_date": "2026-08-08",
    "source": "外购", "count": 4,
}, headers=headers)
if r.status_code == 200 and r.json()["code"] == 200:
    data = r.json()["data"]
    print(f"  批量入栏成功！分配方案：")
    for alloc in data.get("plan", []):
        print(f"    圈舍ID={alloc['pen_id']}({alloc.get('pen_code','')}) 分配={alloc['count']}只 耳标={alloc['ear_tags']}")
else:
    print(f"  -> {r.json()}")

# ============================================================
# 6. 创建饲喂方案（3 套）
# ============================================================
print("\n[6/9] 创建饲喂方案...")
plans = []
for plan_data in [
    {
        "species": "cattle", "plan_name": "育肥牛标准方案", "applicable_stage": "育肥期",
        "applicable_pen_type": "B", "feed_times_per_day": 2,
        "concentrate_weight": 3.0, "silage_weight": 6.0, "hay_weight": 1.5,
        "concentrate_price": 3200, "silage_price": 600, "hay_price": 1200,
        "remark": "适用育肥期牛只，每日2次",
    },
    {
        "species": "cattle", "plan_name": "犊牛保育方案", "applicable_stage": "保育期",
        "applicable_pen_type": "A", "feed_times_per_day": 3,
        "concentrate_weight": 1.0, "silage_weight": 2.0, "hay_weight": 0.5,
        "concentrate_price": 3800, "silage_price": 700, "hay_price": 1500,
        "remark": "犊牛每日3次，饲料质量好",
    },
    {
        "species": "sheep", "plan_name": "育成羊方案", "applicable_stage": "育肥期",
        "applicable_pen_type": "B", "feed_times_per_day": 2,
        "concentrate_weight": 0.5, "silage_weight": 1.5, "hay_weight": 0.8,
        "concentrate_price": 3400, "silage_price": 650, "hay_price": 1100,
        "remark": "育成羊每日2次",
    },
]:
    r = client.post("/api/v1/feeding/plan/add", json=plan_data, headers=headers)
    if r.status_code == 200 and r.json()["code"] == 200:
        d = r.json()["data"]
        plans.append(d)
        print(f"  方案：{d['plan_name']}  ID={d['id']}  预计日成本={d['est_cost_per_day']}元/只")
    else:
        print(f"  -> {r.json()}")

plan_cattle_fattening = next((p["id"] for p in plans if p["plan_name"] == "育肥牛标准方案"), None)
plan_cattle_calf = next((p["id"] for p in plans if p["plan_name"] == "犊牛保育方案"), None)
plan_sheep = next((p["id"] for p in plans if p["plan_name"] == "育成羊方案"), None)

# ============================================================
# 7. 提交饲喂记录（包含待审核、已通过、已驳回三种状态）
# ============================================================
print("\n[7/9] 提交饲喂记录...")
records_to_audit = []
feeding_records = [
    # 今天早上的（已审核通过）
    {"feed_date": "2026-08-10", "time_period": "早", "pen_id": pen_b01, "plan_id": plan_cattle_fattening,
     "actual_concentrate": 36.0, "actual_silage": 72.0, "actual_hay": 18.0, "animal_count": 12,
     "status": "已投喂", "remark": "早班正常投喂"},
    # 今天晚上的（待审核）
    {"feed_date": "2026-08-10", "time_period": "晚", "pen_id": pen_b01, "plan_id": plan_cattle_fattening,
     "actual_concentrate": 35.0, "actual_silage": 70.0, "actual_hay": 17.0, "animal_count": 12,
     "status": "已投喂", "remark": "晚班正常投喂"},
    # 今天早上犊牛舍（待审核）
    {"feed_date": "2026-08-10", "time_period": "早", "pen_id": pen_a01, "plan_id": plan_cattle_calf,
     "actual_concentrate": 2.0, "actual_silage": 4.0, "actual_hay": 1.0, "animal_count": 2,
     "status": "已投喂", "remark": "犊牛少量投喂"},
    # 昨天早上的（已审核通过）
    {"feed_date": "2026-08-09", "time_period": "早", "pen_id": pen_b01, "plan_id": plan_cattle_fattening,
     "actual_concentrate": 36.0, "actual_silage": 72.0, "actual_hay": 18.0, "animal_count": 12,
     "status": "已投喂", "remark": "昨日早班"},
    # 昨天早上的羊舍（待审核）
    {"feed_date": "2026-08-09", "time_period": "早", "pen_id": pen_b02, "plan_id": plan_sheep,
     "actual_concentrate": 1.0, "actual_silage": 3.0, "actual_hay": 1.6, "animal_count": 2,
     "status": "已投喂", "remark": "羊舍投喂"},
]
for rec in feeding_records:
    r = client.post("/api/v1/feeding/record/add", json=rec, headers=headers)
    if r.status_code == 200 and r.json()["code"] == 200:
        d = r.json()["data"]
        print(f"  记录ID={d['id']} 日期={d['feed_date']} {d['time_period']} 圈舍={d['pen_id']} 审核={d['audit_status']} 成本={d['feed_cost']}元")
        if d["audit_status"] == "待审核":
            records_to_audit.append(d["id"])
    else:
        print(f"  -> {r.json()}")

# ============================================================
# 8. 场主审核前几条记录（让数据有"通过"和"驳回"两种状态）
# ============================================================
print("\n[8/9] 场主审核部分饲喂记录...")
# 第1条通过（今天早上的 B01）
if records_to_audit:
    r = client.post(f"/api/v1/feeding/record/audit/{records_to_audit[0]}",
        json={"audit_status": "通过", "remark": "确认无误"}, headers=headers)
    print(f"  记录ID={records_to_audit[0]} 通过 -> {r.json()['msg']}")

# 列表里第一条已通过的（昨天早上的）也审核一下，让它真的变成"通过"
# 实际上前面的 8/09 那条原本就是"待审核"，需要审核
# 把剩下待审核的最后一条驳回
if len(records_to_audit) >= 2:
    # 找一条做驳回演示
    r = client.post(f"/api/v1/feeding/record/audit/{records_to_audit[-1]}",
        json={"audit_status": "驳回", "remark": "投喂量与方案差距过大，请核实"}, headers=headers)
    print(f"  记录ID={records_to_audit[-1]} 驳回 -> {r.json()['msg']}")

# ============================================================
# 9. 物资库存初始化（库存档案 + 进货 + 领用）
# ============================================================
print("\n[9/9] 物资库存初始化...")

# 9.1 新增库存档案（先建档案，库存数量为 0，后续通过进货审核增加）
stock_map = {}  # (material_type, material_name) -> stock_id
print("  --- 新增库存档案 ---")
for stock_data in [
    # 饲料类
    {"material_type": "饲料", "material_name": "玉米精料", "specification": "50kg/袋",
     "quantity": 0, "unit": "kg", "warning_threshold": 200, "remark": "育肥牛精料"},
    {"material_type": "饲料", "material_name": "青贮玉米", "specification": "散装",
     "quantity": 0, "unit": "kg", "warning_threshold": 500, "remark": "青贮饲料"},
    {"material_type": "饲料", "material_name": "羊草干草", "specification": "30kg/捆",
     "quantity": 0, "unit": "kg", "warning_threshold": 100, "remark": "干草饲料"},
    # 疫苗类
    {"material_type": "疫苗", "material_name": "口蹄疫疫苗", "specification": "100ml/瓶",
     "quantity": 0, "unit": "瓶", "warning_threshold": 5, "remark": "口蹄疫预防"},
    {"material_type": "疫苗", "material_name": "牛结节性皮肤病疫苗", "specification": "50头份/瓶",
     "quantity": 0, "unit": "瓶", "warning_threshold": 3, "remark": "结节性皮肤病预防"},
    # 兽药类
    {"material_type": "兽药", "material_name": "青霉素钠", "specification": "160万单位/瓶",
     "quantity": 0, "unit": "瓶", "warning_threshold": 10, "remark": "广谱抗生素"},
    {"material_type": "兽药", "material_name": "维生素ADE注射液", "specification": "10ml/盒",
     "quantity": 0, "unit": "盒", "warning_threshold": 5, "remark": "营养补充剂"},
]:
    r = client.post("/api/v1/inventory/stock/add", json=stock_data, headers=headers)
    if r.status_code == 200 and r.json()["code"] == 200:
        d = r.json()["data"]
        stock_map[(d["material_type"], d["material_name"])] = d["id"]
        print(f"  库存ID={d['id']}  {d['material_type']}/{d['material_name']}  阈值={d.get('warning_threshold')}")
    else:
        print(f"  {stock_data['material_name']} -> {r.json()}")

# 9.2 提交进货记录并自动审核通过（让库存有真实数据）
print("  --- 提交进货记录（自动审核通过）---")
purchase_records = [
    {"material_type": "饲料", "material_name": "玉米精料", "batch_no": "YL20260701",
     "quantity": 2000, "unit": "kg", "cost_price": 3.2,
     "production_date": "2026-07-01", "expiry_date": "2026-12-01",
     "supplier": "本地饲料厂", "purchase_date": "2026-07-15"},
    {"material_type": "饲料", "material_name": "青贮玉米", "batch_no": "QC20260801",
     "quantity": 5000, "unit": "kg", "cost_price": 0.6,
     "production_date": "2026-08-01", "expiry_date": "2027-02-01",
     "supplier": "本村青贮窖", "purchase_date": "2026-08-05"},
    {"material_type": "饲料", "material_name": "羊草干草", "batch_no": "YC20260801",
     "quantity": 800, "unit": "kg", "cost_price": 1.2,
     "production_date": "2026-07-15", "expiry_date": "2027-01-15",
     "supplier": "内蒙古草业", "purchase_date": "2026-08-08"},
    {"material_type": "疫苗", "material_name": "口蹄疫疫苗", "batch_no": "VAC20260601",
     "quantity": 20, "unit": "瓶", "cost_price": 45.0,
     "production_date": "2026-06-01", "expiry_date": "2027-06-01",
     "supplier": "县动物疾控中心", "purchase_date": "2026-06-10"},
    {"material_type": "兽药", "material_name": "青霉素钠", "batch_no": "MED20260701",
     "quantity": 30, "unit": "瓶", "cost_price": 8.5,
     "production_date": "2026-07-01", "expiry_date": "2027-07-01",
     "supplier": "兽药经销商", "purchase_date": "2026-07-20"},
]
purchases_to_audit = []
for pur in purchase_records:
    r = client.post("/api/v1/inventory/purchase/add", json=pur, headers=headers)
    if r.status_code == 200 and r.json()["code"] == 200:
        d = r.json()["data"]
        purchases_to_audit.append(d["id"])
        print(f"  进货ID={d['id']}  {d['material_type']}/{d['material_name']}  数量={d['quantity']}{d['unit']}  金额={d['total_cost']}元  审核={d['audit_status']}")
    else:
        print(f"  {pur['material_name']} -> {r.json()}")

# 场主批量审核通过进货记录
print("  --- 场主审核通过进货记录（自动增加库存）---")
for pid in purchases_to_audit:
    r = client.post(f"/api/v1/inventory/purchase/audit/{pid}",
                    json={"audit_status": "通过", "remark": "验收入库"}, headers=headers)
    if r.status_code == 200 and r.json()["code"] == 200:
        d = r.json()["data"]
        print(f"  进货ID={pid} 通过  关联库存ID={d['stock_id']}  {d['material_name']}")

# 9.3 提交领用记录（部分审核通过，部分待审核）
print("  --- 提交领用记录 ---")
consume_records = [
    # 已审核通过：今天早班育肥牛饲喂用精料
    {"stock_id": stock_map.get(("饲料", "玉米精料")), "quantity": 36.0, "unit": "kg",
     "consume_date": "2026-08-10", "related_module": "饲喂", "remark": "B02 早班育肥牛投喂"},
    # 已审核通过：今天早班青贮
    {"stock_id": stock_map.get(("饲料", "青贮玉米")), "quantity": 72.0, "unit": "kg",
     "consume_date": "2026-08-10", "related_module": "饲喂", "remark": "B02 早班青贮投喂"},
    # 待审核：今天晚班精料
    {"stock_id": stock_map.get(("饲料", "玉米精料")), "quantity": 35.0, "unit": "kg",
     "consume_date": "2026-08-10", "related_module": "饲喂", "remark": "B02 晚班育肥牛投喂"},
    # 待审核：犊牛保育用精料
    {"stock_id": stock_map.get(("饲料", "玉米精料")), "quantity": 2.0, "unit": "kg",
     "consume_date": "2026-08-10", "related_module": "饲喂", "remark": "A01 犊牛投喂"},
]
consumes_to_audit = []
for con in consume_records:
    if not con["stock_id"]:
        print(f"  跳过：找不到库存ID  {con['remark']}")
        continue
    r = client.post("/api/v1/inventory/consume/add", json=con, headers=headers)
    if r.status_code == 200 and r.json()["code"] == 200:
        d = r.json()["data"]
        consumes_to_audit.append(d["id"])
        print(f"  领用ID={d['id']}  {d['material_name']}  数量={d['quantity']}{d['unit']}  审核={d['audit_status']}  关联={d.get('related_module')}")
    else:
        print(f"  {con['remark']} -> {r.json()}")

# 场主审核前两条领用（让数据有通过 + 待审核两种状态）
print("  --- 场主审核部分领用记录 ---")
for cid in consumes_to_audit[:2]:
    r = client.post(f"/api/v1/inventory/consume/audit/{cid}",
                    json={"audit_status": "通过", "remark": "确认领用"}, headers=headers)
    if r.status_code == 200 and r.json()["code"] == 200:
        print(f"  领用ID={cid} 通过  {r.json()['data']['material_name']}")

# ============================================================
# 总结输出
# ============================================================
print("\n" + "=" * 70)
print("  数据初始化完成！登录信息：")
print("=" * 70)
print(f"  场主账号：sunshine / 123456  (user_type=2)")
print(f"  饲喂员1：feeder01 / 123456   (user_type=3, post=饲喂员)")
print(f"  饲喂员2：feeder02 / 123456   (user_type=3, post=饲喂员)")
print(f"  兽医：    vet01 / 123456     (user_type=3, post=兽医)")
print(f"  超管：    admin / admin123   (user_type=1)")
print()
print("  数据概况：")
print(f"  - 圈舍：{len(pens)} 个（A/B/C/D 四类）")
print(f"  - 畜禽：12 只（个体入栏 8 + 批量入栏 4）")
print(f"  - 饲喂方案：{len(plans)} 套")
print(f"  - 饲喂记录：{len(feeding_records)} 条（含通过/待审核/驳回三种状态）")
print(f"  - 物资库存：{len(stock_map)} 种（饲料/疫苗/兽药三类）")
print(f"  - 进货记录：{len(purchase_records)} 条（全部审核通过，库存已增加）")
print(f"  - 领用记录：{len(consume_records)} 条（含通过/待审核两种状态）")
print("=" * 70)

# ===== 9. 输出当前所有数据（便于核对）=====
print("\n========== 数据库当前数据快照 ==========")

with _session_factory() as db:
    print("\n--- sys_user ---")
    rows = db.execute(text("SELECT id, username, real_name, user_type, farm_id, post FROM sys_user WHERE deleted=0"))
    for r in rows:
        print(f"  {r}")

    print("\n--- farm_info ---")
    rows = db.execute(text("SELECT id, farm_name, owner_user_id, livestock_types FROM farm_info WHERE deleted=0"))
    for r in rows:
        print(f"  {r}")

    print("\n--- pen_info ---")
    rows = db.execute(text("SELECT id, farm_id, pen_code, species, pen_type, capacity, current_count FROM pen_info WHERE deleted=0"))
    for r in rows:
        print(f"  {r}")

    print("\n--- animal_archive ---")
    rows = db.execute(text("SELECT id, farm_id, ear_tag, species, breed, gender, pen_id, growth_stage, status FROM animal_archive WHERE deleted=0"))
    for r in rows:
        print(f"  {r}")

    print("\n--- feeding_plan ---")
    rows = db.execute(text("SELECT id, farm_id, species, plan_name, applicable_stage, feed_times_per_day, est_cost_per_day, status FROM feeding_plan WHERE deleted=0"))
    for r in rows:
        print(f"  {r}")

    print("\n--- feeding_record ---")
    rows = db.execute(text("SELECT id, farm_id, feed_date, time_period, pen_id, plan_id, animal_count, feed_cost, status, audit_status FROM feeding_record WHERE deleted=0"))
    for r in rows:
        print(f"  {r}")

    print("\n--- material_stock ---")
    rows = db.execute(text("SELECT id, farm_id, material_type, material_name, quantity, unit, warning_threshold, expiry_date, status, is_shortage FROM material_stock WHERE deleted=0"))
    for r in rows:
        print(f"  {r}")

    print("\n--- material_purchase ---")
    rows = db.execute(text("SELECT id, farm_id, stock_id, material_type, material_name, quantity, unit, cost_price, total_cost, purchase_date, audit_status FROM material_purchase WHERE deleted=0"))
    for r in rows:
        print(f"  {r}")

    print("\n--- material_consume ---")
    rows = db.execute(text("SELECT id, farm_id, stock_id, material_type, material_name, quantity, unit, consume_date, related_module, status, audit_status FROM material_consume WHERE deleted=0"))
    for r in rows:
        print(f"  {r}")

print("\n完成。")
