"""
八戒牧场测试数据初始化脚本

通过 TestClient 调用真实 API，为「八戒牧场」(farm_id=5) 生成配套数据：
- 自动 bcrypt 哈希密码（登录 bajie 账号拿 token）
- 自动耳标生成 + 圈舍自动分配 + 生长阶段判定
- 自动饲喂成本 / 库存状态维护

仅操作八戒牧场的数据，不影响阳光牧场。
如需清空八戒牧场的旧数据再重建，加上 --reset 参数。

执行方式：
    cd livestock_server
    BAJIE_PASSWORD=你的密码 python init_bajie_data.py            # 写入真实 MySQL
    BAJIE_PASSWORD=你的密码 python init_bajie_data.py --reset    # 先清空八戒牧场数据再重建
    BAJIE_PASSWORD=你的密码 python init_bajie_data.py --sqlite   # SQLite 内存库（仅打印验证，不持久化）
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ===== 1. 选择数据库引擎 =====
USE_SQLITE = "--sqlite" in sys.argv
RESET = "--reset" in sys.argv

if USE_SQLITE:
    _engine = create_engine(
        "sqlite://",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    print("[模式] SQLite 内存库（数据不持久化，仅打印验证）")
else:
    from app.config import settings
    _engine = create_engine(settings.db_url, echo=False, pool_pre_ping=True)
    print(f"[模式] MySQL 真实数据库：{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

# 替换 app.database 的 engine（必须在 import app.main 之前）
import app.database as db_mod
db_mod.engine = _engine
db_mod.SessionLocal = _session_factory

from app.database import Base
import app.models  # noqa
from app.main import app
from app.core.security import hash_password
from app.models.user import User

# ===== 2. 建表（如果不存在）=====
Base.metadata.create_all(bind=_engine)

# ===== 3. 读取 bajie 密码 =====
BAJIE_PASSWORD = os.environ.get("BAJIE_PASSWORD", "")
if not BAJIE_PASSWORD:
    print("请通过环境变量指定 bajie 账号密码：")
    print("    BAJIE_PASSWORD=你的密码 python init_bajie_data.py")
    sys.exit(1)

from fastapi.testclient import TestClient
client = TestClient(app)

print("=" * 70)
print("  八戒牧场 - 测试数据初始化")
print("=" * 70)

# ============================================================
# 0. 定位八戒牧场并登录场主账号
# ============================================================
print("\n[0/9] 定位八戒牧场并登录场主账号...")
login = client.post("/api/v1/auth/login", json={"username": "bajie", "password": BAJIE_PASSWORD})
if login.status_code != 200 or login.json().get("code") != 200:
    # 账号不存在：自动注册八戒牧场 + 场主账号（保证 --sqlite 验证也能跑通）
    print(f"  bajie 账号不存在，尝试注册八戒牧场场主账号...")
    reg = client.post("/api/v1/auth/register/owner", json={
        "farm_name": "八戒牧场",
        "username": "bajie",
        "password": BAJIE_PASSWORD,
        "real_name": "猪八戒",
        "phone": "13900000099",
        "livestock_types": "猪",
    })
    print(f"  注册 -> {reg.json()}")
    login = client.post("/api/v1/auth/login", json={"username": "bajie", "password": BAJIE_PASSWORD})
    if login.status_code != 200 or login.json().get("code") != 200:
        print(f"  -> 登录失败：{login.json()}")
        sys.exit(1)
owner_token = login.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {owner_token}"}

farm_info = client.get("/api/v1/farm/info", headers=headers).json()["data"]
farm_id = farm_info["id"]
print(f"  养殖场ID={farm_id}  名称={farm_info['farm_name']}  种类={farm_info['livestock_types']}")
if farm_info["farm_name"] != "八戒牧场":
    print(f"  !! 注意：当前账号对应养殖场不是「八戒牧场」，脚本可能操作了错误的农场，已中止。")
    sys.exit(1)

# ===== 4. --reset：清空八戒牧场的历史数据 =====
if RESET and not USE_SQLITE:
    print("\n[reset] 清空八戒牧场旧数据...")
    with _engine.connect() as conn:
        tables = ["material_consume", "material_purchase", "material_stock",
                  "feeding_record", "feeding_plan", "animal_archive_history",
                  "animal_archive", "pen_info"]
        for t in tables:
            try:
                conn.execute(text(f"DELETE FROM {t} WHERE farm_id={farm_id}"))
                print(f"  - {t} (farm_id={farm_id}) 已清空")
            except Exception as e:
                print(f"  - {t} 跳过：{e}")
        conn.commit()

# ============================================================
# 1. 创建圈舍（猪场：仔猪/保育/育成/繁育/种公猪舍）
#    耳标 5 位规则：畜种位(猪=3) + 圈舍编号数字(2位) + 入栏序号(2位)，
#    要求同畜种内编号数字唯一，故 8 个猪舍编号数字连续 01-08（A01/A02/B03/.../D08）
# ============================================================
print("\n[1/9] 创建圈舍...")
pens = []
for pen_code, pen_type, capacity, remark in [
    ("A01", "A", 12, "仔猪保育舍"),
    ("A02", "A", 12, "保育猪舍"),
    ("B03", "B", 12, "育成猪舍"),
    ("B04", "B", 12, "育肥猪舍"),
    ("B05", "B", 12, "育肥猪舍2"),
    ("C06", "C", 6, "母猪繁育舍"),
    ("C07", "C", 6, "后备母猪舍"),
    ("D08", "D", 1, "种公猪舍"),
]:
    r = client.post("/api/v1/pen/add", json={
        "pen_code": pen_code, "pen_type": pen_type,
        "capacity": capacity, "remark": remark, "species": "猪",
    }, headers=headers)
    if r.status_code == 200 and r.json()["code"] == 200:
        pens.append({"id": r.json()["data"]["id"], "code": pen_code, "type": pen_type})
        print(f"  {pen_code} ({pen_type}类) -> ID={r.json()['data']['id']}  {remark}")
    else:
        print(f"  {pen_code} -> {r.json()}")

pen_a01 = next((p["id"] for p in pens if p["code"] == "A01"), None)
pen_a02 = next((p["id"] for p in pens if p["code"] == "A02"), None)
pen_b03 = next((p["id"] for p in pens if p["code"] == "B03"), None)
pen_b04 = next((p["id"] for p in pens if p["code"] == "B04"), None)
pen_b05 = next((p["id"] for p in pens if p["code"] == "B05"), None)
pen_c06 = next((p["id"] for p in pens if p["code"] == "C06"), None)
pen_c07 = next((p["id"] for p in pens if p["code"] == "C07"), None)
pen_d08 = next((p["id"] for p in pens if p["code"] == "D08"), None)

# ============================================================
# 2. 个体入栏（猪：不同阶段进不同圈舍）
# ============================================================
print("\n[2/9] 个体入栏...")
animals = [
    # 仔猪（A01）
    {"species": "猪", "breed": "大白猪", "gender": "母", "birth_date": "2026-07-20", "in_date": "2026-08-01", "source": "自繁", "pen_id": pen_a01, "remark": "仔猪"},
    {"species": "猪", "breed": "大白猪", "gender": "公", "birth_date": "2026-07-22", "in_date": "2026-08-02", "source": "自繁", "pen_id": pen_a01, "remark": "仔猪"},
    {"species": "猪", "breed": "长白猪", "gender": "母", "birth_date": "2026-07-25", "in_date": "2026-08-03", "source": "外购", "pen_id": pen_a01, "remark": "仔猪"},
    # 保育猪（A02）
    {"species": "猪", "breed": "大白猪", "gender": "母", "birth_date": "2026-06-05", "in_date": "2026-07-01", "source": "自繁", "pen_id": pen_a02, "remark": "保育期"},
    {"species": "猪", "breed": "杜洛克", "gender": "公", "birth_date": "2026-06-10", "in_date": "2026-07-05", "source": "外购", "pen_id": pen_a02, "remark": "保育期"},
    # 育成猪（B03）
    {"species": "猪", "breed": "长白猪", "gender": "母", "birth_date": "2026-04-15", "in_date": "2026-05-20", "source": "自繁", "pen_id": pen_b03, "remark": "生长期"},
    {"species": "猪", "breed": "大白猪", "gender": "母", "birth_date": "2026-04-20", "in_date": "2026-05-25", "source": "自繁", "pen_id": pen_b03, "remark": "生长期"},
    # 育肥猪（B04）
    {"species": "猪", "breed": "大白猪", "gender": "公", "birth_date": "2026-03-01", "in_date": "2026-04-10", "source": "外购", "pen_id": pen_b04, "remark": "育肥期"},
    {"species": "猪", "breed": "长白猪", "gender": "公", "birth_date": "2026-03-05", "in_date": "2026-04-15", "source": "外购", "pen_id": pen_b04, "remark": "育肥期"},
    # 可繁育母猪（C06）
    {"species": "猪", "breed": "大白猪", "gender": "母", "birth_date": "2025-10-01", "in_date": "2026-01-01", "source": "外购", "pen_id": pen_c06, "remark": "可繁育母猪"},
    {"species": "猪", "breed": "长白猪", "gender": "母", "birth_date": "2025-11-15", "in_date": "2026-02-01", "source": "外购", "pen_id": pen_c06, "remark": "可繁育母猪"},
    # 后备母猪（C07）
    {"species": "猪", "breed": "杜洛克", "gender": "母", "birth_date": "2026-01-10", "in_date": "2026-03-01", "source": "外购", "pen_id": pen_c07, "remark": "后备母猪"},
    # 种公猪（D08）
    {"species": "猪", "breed": "杜洛克", "gender": "公", "birth_date": "2024-05-01", "in_date": "2025-01-01", "source": "外购", "pen_id": pen_d08, "remark": "种公猪"},
]
for a in animals:
    if not a["pen_id"]:
        print(f"  {a['species']}({a['breed']}) 跳过：圈舍未创建")
        continue
    r = client.post("/api/v1/animal/individual", json=a, headers=headers)
    if r.status_code == 200 and r.json()["code"] == 200:
        d = r.json()["data"]
        print(f"  {d['species']}({d['breed']}) 耳标={d['ear_tag']} 圈舍ID={d['pen_id']} 阶段={d['growth_stage']}")
    else:
        print(f"  {a['species']}({a['breed']}) -> {r.json()}")

# ============================================================
# 3. 批量入栏（8 头育肥猪，自动分配）
# ============================================================
print("\n[3/9] 批量入栏 8 头育肥猪...")
r = client.post("/api/v1/animal/batch", json={
    "species": "猪", "breed": "大白猪", "gender": "母",
    "birth_date": "2026-02-15", "in_date": "2026-08-08",
    "source": "外购", "count": 8,
}, headers=headers)
if r.status_code == 200 and r.json()["code"] == 200:
    data = r.json()["data"]
    print(f"  批量入栏成功！分配方案：")
    for alloc in data.get("plan", []):
        print(f"    圈舍ID={alloc['pen_id']}({alloc.get('pen_code','')}) 分配={alloc['count']}只 耳标={alloc['ear_tags']}")
else:
    print(f"  -> {r.json()}")

# ============================================================
# 4. 创建饲喂方案（猪用 3 套）
# ============================================================
print("\n[4/9] 创建饲喂方案...")
plans = []
for plan_data in [
    {
        "species": "pig", "plan_name": "育肥猪标准方案", "applicable_stage": "育肥期",
        "applicable_pen_type": "B", "feed_times_per_day": 2,
        "concentrate_weight": 1.8, "silage_weight": 0, "hay_weight": 0,
        "concentrate_price": 3600, "silage_price": None, "hay_price": None,
        "remark": "育肥猪每日2次，全价配合饲料",
    },
    {
        "species": "pig", "plan_name": "仔猪保育方案", "applicable_stage": "保育期",
        "applicable_pen_type": "A", "feed_times_per_day": 3,
        "concentrate_weight": 0.4, "silage_weight": 0, "hay_weight": 0,
        "concentrate_price": 5200, "silage_price": None, "hay_price": None,
        "remark": "仔猪保育料，每日3次",
    },
    {
        "species": "pig", "plan_name": "繁育母猪方案", "applicable_stage": "繁育期",
        "applicable_pen_type": "C", "feed_times_per_day": 2,
        "concentrate_weight": 2.5, "silage_weight": 0.5, "hay_weight": 0,
        "concentrate_price": 4200, "silage_price": 500, "hay_price": None,
        "remark": "妊娠/哺乳母猪，每日2次",
    },
]:
    r = client.post("/api/v1/feeding/plan/add", json=plan_data, headers=headers)
    if r.status_code == 200 and r.json()["code"] == 200:
        d = r.json()["data"]
        plans.append(d)
        print(f"  方案：{d['plan_name']}  ID={d['id']}  预计日成本={d['est_cost_per_day']}元/只")
    else:
        print(f"  -> {r.json()}")

plan_fatten = next((p["id"] for p in plans if p["plan_name"] == "育肥猪标准方案"), None)
plan_calf = next((p["id"] for p in plans if p["plan_name"] == "仔猪保育方案"), None)
plan_breed = next((p["id"] for p in plans if p["plan_name"] == "繁育母猪方案"), None)

# ============================================================
# 5. 提交饲喂记录（含待审核/通过/驳回三种状态）
# ============================================================
print("\n[5/9] 提交饲喂记录...")
records_to_audit = []
feeding_records = [
    # 今天早上的育肥猪舍（已通过）
    {"feed_date": "2026-08-10", "time_period": "早", "pen_id": pen_b04, "plan_id": plan_fatten,
     "actual_concentrate": 18.0, "actual_silage": None, "actual_hay": None, "animal_count": 10,
     "status": "已投喂", "remark": "早班正常投喂"},
    # 今天晚上的育肥猪舍（待审核）
    {"feed_date": "2026-08-10", "time_period": "晚", "pen_id": pen_b04, "plan_id": plan_fatten,
     "actual_concentrate": 17.5, "actual_silage": None, "actual_hay": None, "animal_count": 10,
     "status": "已投喂", "remark": "晚班正常投喂"},
    # 今天早上保育舍（待审核）
    {"feed_date": "2026-08-10", "time_period": "早", "pen_id": pen_a02, "plan_id": plan_calf,
     "actual_concentrate": 0.8, "actual_silage": None, "actual_hay": None, "animal_count": 2,
     "status": "已投喂", "remark": "保育猪投喂"},
    # 昨天早上育肥猪舍（已通过）
    {"feed_date": "2026-08-09", "time_period": "早", "pen_id": pen_b04, "plan_id": plan_fatten,
     "actual_concentrate": 18.0, "actual_silage": None, "actual_hay": None, "animal_count": 10,
     "status": "已投喂", "remark": "昨日早班"},
    # 昨天早上繁育母猪（待审核）
    {"feed_date": "2026-08-09", "time_period": "早", "pen_id": pen_c06, "plan_id": plan_breed,
     "actual_concentrate": 5.0, "actual_silage": 1.0, "actual_hay": None, "animal_count": 2,
     "status": "已投喂", "remark": "繁育母猪投喂"},
]
for rec in feeding_records:
    if not rec["pen_id"]:
        print(f"  跳过：圈舍未创建  {rec['remark']}")
        continue
    r = client.post("/api/v1/feeding/record/add", json=rec, headers=headers)
    if r.status_code == 200 and r.json()["code"] == 200:
        d = r.json()["data"]
        print(f"  记录ID={d['id']} 日期={d['feed_date']} {d['time_period']} 圈舍={d['pen_id']} 审核={d['audit_status']} 成本={d['feed_cost']}元")
        if d["audit_status"] == "待审核":
            records_to_audit.append(d["id"])
    else:
        print(f"  -> {r.json()}")

# ============================================================
# 6. 场主审核饲喂记录
# ============================================================
print("\n[6/9] 场主审核部分饲喂记录...")
if records_to_audit:
    r = client.post(f"/api/v1/feeding/record/audit/{records_to_audit[0]}",
        json={"audit_status": "通过", "remark": "确认无误"}, headers=headers)
    print(f"  记录ID={records_to_audit[0]} 通过 -> {r.json()['msg']}")
if len(records_to_audit) >= 2:
    r = client.post(f"/api/v1/feeding/record/audit/{records_to_audit[-1]}",
        json={"audit_status": "驳回", "remark": "投喂量与方案差距过大，请核实"}, headers=headers)
    print(f"  记录ID={records_to_audit[-1]} 驳回 -> {r.json()['msg']}")

# ============================================================
# 7. 物资库存初始化（猪场常用物资）
# ============================================================
print("\n[7/9] 物资库存初始化...")

# 7.1 新增库存档案
stock_map = {}
print("  --- 新增库存档案 ---")
for stock_data in [
    # 饲料类
    {"material_type": "饲料", "material_name": "猪全价配合料", "specification": "40kg/袋",
     "quantity": 0, "unit": "kg", "warning_threshold": 300, "remark": "育肥猪全价料"},
    {"material_type": "饲料", "material_name": "仔猪保育料", "specification": "20kg/袋",
     "quantity": 0, "unit": "kg", "warning_threshold": 100, "remark": "仔猪保育料"},
    {"material_type": "饲料", "material_name": "母猪妊娠料", "specification": "40kg/袋",
     "quantity": 0, "unit": "kg", "warning_threshold": 150, "remark": "妊娠/哺乳母猪料"},
    # 疫苗类
    {"material_type": "疫苗", "material_name": "猪瘟疫苗", "specification": "100ml/瓶",
     "quantity": 0, "unit": "瓶", "warning_threshold": 5, "remark": "猪瘟预防"},
    {"material_type": "疫苗", "material_name": "口蹄疫疫苗（猪）", "specification": "100ml/瓶",
     "quantity": 0, "unit": "瓶", "warning_threshold": 5, "remark": "口蹄疫预防"},
    # 兽药类
    {"material_type": "兽药", "material_name": "阿莫西林可溶性粉", "specification": "100g/袋",
     "quantity": 0, "unit": "袋", "warning_threshold": 20, "remark": "呼吸道/肠道感染"},
    {"material_type": "兽药", "material_name": "电解多维", "specification": "500g/袋",
     "quantity": 0, "unit": "袋", "warning_threshold": 10, "remark": "抗应激营养补充"},
]:
    r = client.post("/api/v1/inventory/stock/add", json=stock_data, headers=headers)
    if r.status_code == 200 and r.json()["code"] == 200:
        d = r.json()["data"]
        stock_map[(d["material_type"], d["material_name"])] = d["id"]
        print(f"  库存ID={d['id']}  {d['material_type']}/{d['material_name']}  阈值={d.get('warning_threshold')}")
    else:
        print(f"  {stock_data['material_name']} -> {r.json()}")

# 7.2 提交进货记录并审核通过
print("  --- 提交进货记录（自动审核通过）---")
purchase_records = [
    {"material_type": "饲料", "material_name": "猪全价配合料", "batch_no": "PJ20260701",
     "quantity": 3000, "unit": "kg", "cost_price": 3.6,
     "production_date": "2026-07-01", "expiry_date": "2026-12-01",
     "supplier": "本地饲料厂", "purchase_date": "2026-07-15"},
    {"material_type": "饲料", "material_name": "仔猪保育料", "batch_no": "ZY20260701",
     "quantity": 800, "unit": "kg", "cost_price": 5.2,
     "production_date": "2026-07-01", "expiry_date": "2026-12-01",
     "supplier": "本地饲料厂", "purchase_date": "2026-07-15"},
    {"material_type": "饲料", "material_name": "母猪妊娠料", "batch_no": "MZ20260701",
     "quantity": 1000, "unit": "kg", "cost_price": 4.2,
     "production_date": "2026-07-01", "expiry_date": "2026-12-01",
     "supplier": "本地饲料厂", "purchase_date": "2026-07-15"},
    {"material_type": "疫苗", "material_name": "猪瘟疫苗", "batch_no": "VAC20260601",
     "quantity": 30, "unit": "瓶", "cost_price": 25.0,
     "production_date": "2026-06-01", "expiry_date": "2027-06-01",
     "supplier": "县动物疾控中心", "purchase_date": "2026-06-10"},
    {"material_type": "兽药", "material_name": "阿莫西林可溶性粉", "batch_no": "MED20260701",
     "quantity": 50, "unit": "袋", "cost_price": 12.0,
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

print("  --- 场主审核通过进货记录（自动增加库存）---")
for pid in purchases_to_audit:
    r = client.post(f"/api/v1/inventory/purchase/audit/{pid}",
                    json={"audit_status": "通过", "remark": "验收入库"}, headers=headers)
    if r.status_code == 200 and r.json()["code"] == 200:
        d = r.json()["data"]
        print(f"  进货ID={pid} 通过  关联库存ID={d['stock_id']}  {d['material_name']}")

# 7.3 提交领用记录（部分通过，部分待审核）
print("  --- 提交领用记录 ---")
consume_records = [
    # 已审核通过：今天早班育肥猪投喂用全价料
    {"stock_id": stock_map.get(("饲料", "猪全价配合料")), "quantity": 18.0, "unit": "kg",
     "consume_date": "2026-08-10", "related_module": "饲喂", "remark": "B04 早班育肥猪投喂"},
    # 待审核：今天晚班育肥猪投喂
    {"stock_id": stock_map.get(("饲料", "猪全价配合料")), "quantity": 17.5, "unit": "kg",
     "consume_date": "2026-08-10", "related_module": "饲喂", "remark": "B04 晚班育肥猪投喂"},
    # 待审核：保育猪投喂保育料
    {"stock_id": stock_map.get(("饲料", "仔猪保育料")), "quantity": 0.8, "unit": "kg",
     "consume_date": "2026-08-10", "related_module": "饲喂", "remark": "A02 保育猪投喂"},
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

print("  --- 场主审核部分领用记录 ---")
for cid in consumes_to_audit[:1]:
    r = client.post(f"/api/v1/inventory/consume/audit/{cid}",
                    json={"audit_status": "通过", "remark": "确认领用"}, headers=headers)
    if r.status_code == 200 and r.json()["code"] == 200:
        print(f"  领用ID={cid} 通过  {r.json()['data']['material_name']}")

# ============================================================
# 总结输出
# ============================================================
print("\n" + "=" * 70)
print("  数据初始化完成！八戒牧场登录信息：")
print("=" * 70)
print(f"  场主账号：bajie / {BAJIE_PASSWORD}  (user_type=2)")
print(f"  超管切换：admin / admin123  (在头部选择八戒牧场)")
print()
print(f"  数据概况：")
print(f"  - 圈舍：{len(pens)} 个（A/B/C/D 四类）")
print(f"  - 畜禽：{len(animals)} 只个体 + 8 头批量入栏")
print(f"  - 饲喂方案：{len(plans)} 套（育肥/保育/繁育）")
print(f"  - 饲喂记录：{len(feeding_records)} 条（含通过/待审核/驳回三种状态）")
print(f"  - 物资库存：{len(stock_map)} 种（饲料/疫苗/兽药三类）")
print(f"  - 进货记录：{len(purchase_records)} 条（全部审核通过，库存已增加）")
print(f"  - 领用记录：{len(consume_records)} 条（含通过/待审核两种状态）")
print("=" * 70)

# ============================================================
# 数据快照（仅 SQLite/有权限时打印）
# ============================================================
print("\n========== 八戒牧场数据快照 ==========")
with _session_factory() as db:
    print("\n--- pen_info ---")
    rows = db.execute(text("SELECT id, farm_id, pen_code, species, pen_type, capacity, current_count FROM pen_info WHERE farm_id=:fid AND deleted=0"), {"fid": farm_id})
    for r in rows:
        print(f"  {r}")

    print("\n--- animal_archive ---")
    rows = db.execute(text("SELECT id, ear_tag, species, breed, gender, pen_id, growth_stage, status FROM animal_archive WHERE farm_id=:fid AND deleted=0"), {"fid": farm_id})
    for r in rows:
        print(f"  {r}")

    print("\n--- feeding_plan ---")
    rows = db.execute(text("SELECT id, plan_name, species, applicable_stage, feed_times_per_day, est_cost_per_day, status FROM feeding_plan WHERE farm_id=:fid AND deleted=0"), {"fid": farm_id})
    for r in rows:
        print(f"  {r}")

    print("\n--- feeding_record ---")
    rows = db.execute(text("SELECT id, feed_date, time_period, pen_id, plan_id, animal_count, feed_cost, status, audit_status FROM feeding_record WHERE farm_id=:fid AND deleted=0"), {"fid": farm_id})
    for r in rows:
        print(f"  {r}")

    print("\n--- material_stock ---")
    rows = db.execute(text("SELECT id, material_type, material_name, quantity, unit, warning_threshold, status, is_shortage FROM material_stock WHERE farm_id=:fid AND deleted=0"), {"fid": farm_id})
    for r in rows:
        print(f"  {r}")

print("\n完成。")
