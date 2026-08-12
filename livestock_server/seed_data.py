"""
批量生成测试畜禽档案数据
牛/羊/猪，不同品种、生长阶段，分配到各个圈舍
"""
import sys
sys.path.insert(0, 'D:/Code/system/livestock_server')

from datetime import date, timedelta
from app.database import SessionLocal, engine, Base
from app.models.animal import Animal
from app.models.pen import Pen
import random

# 确保表存在
Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    # 先清空已有测试数据
    db.query(Animal).delete()
    db.commit()

    # 更新圈舍存栏数为 0
    pens = db.query(Pen).all()
    for p in pens:
        p.current_count = 0
    db.commit()

    # pen_code -> pen_id 映射
    pen_map = {p.pen_code: p.id for p in pens}
    print(f"圈舍映射: {pen_map}")

    cattle_breeds = ['黄牛', '西门塔尔牛', '荷斯坦牛', '安格斯牛', '夏洛莱牛']
    sheep_breeds = ['小尾寒羊', '湖羊', '杜泊羊', '波尔山羊']
    pig_breeds = ['长白猪', '大白猪', '杜洛克', '皮特兰']

    animals = []
    ear_tag_pool = {
        'A01': 1, 'A02': 1, 'A03': 1,
        'B01': 1, 'B02': 1, 'B03': 1,
        'C01': 1, 'C02': 1, 'D01': 1,
    }

    def next_tag(pen_code):
        seq = ear_tag_pool.get(pen_code, 1)
        ear_tag_pool[pen_code] = seq + 1
        return f"{pen_code.replace('A','').replace('B','').replace('C','').replace('D','')}{seq:02d}"

    # ===== 牛的档案 (A类+ B类圈舍) =====
    cattle_data = [
        # A01 (犊牛: 1-60天)
        {'pen': 'A01', 'breed': random.choice(cattle_breeds), 'gender': '母', 'birth': date(2026, 7, 1), 'source': '自繁', 'stage': '犊牛期'},
        {'pen': 'A01', 'breed': random.choice(cattle_breeds), 'gender': '母', 'birth': date(2026, 6, 20), 'source': '自繁', 'stage': '保育期'},
        {'pen': 'A01', 'breed': random.choice(cattle_breeds), 'gender': '公', 'birth': date(2026, 7, 10), 'source': '外购', 'stage': '犊牛期'},
        {'pen': 'A01', 'breed': random.choice(cattle_breeds), 'gender': '母', 'birth': date(2026, 6, 15), 'source': '自繁', 'stage': '保育期'},
        {'pen': 'A01', 'breed': random.choice(cattle_breeds), 'gender': '公', 'birth': date(2026, 7, 5), 'source': '外购', 'stage': '犊牛期'},
        {'pen': 'A01', 'breed': random.choice(cattle_breeds), 'gender': '母', 'birth': date(2026, 5, 1), 'source': '自繁', 'stage': '保育期'},
        {'pen': 'A01', 'breed': random.choice(cattle_breeds), 'gender': '母', 'birth': date(2026, 6, 1), 'source': '外购', 'stage': '保育期'},
        {'pen': 'A01', 'breed': random.choice(cattle_breeds), 'gender': '公', 'birth': date(2026, 7, 15), 'source': '自繁', 'stage': '犊牛期'},
        {'pen': 'A01', 'breed': random.choice(cattle_breeds), 'gender': '母', 'birth': date(2026, 6, 10), 'source': '外购', 'stage': '保育期'},
        {'pen': 'A01', 'breed': random.choice(cattle_breeds), 'gender': '公', 'birth': date(2026, 5, 20), 'source': '自繁', 'stage': '保育期'},
    ]

    # A02
    for _ in range(8):
        d = date(2026, random.randint(1, 8), random.randint(1, 28))
        cattle_data.append({'pen': 'A02', 'breed': random.choice(cattle_breeds), 'gender': random.choice(['公','母']), 'birth': d, 'source': random.choice(['自繁','外购']), 'stage': '犊牛期' if d > date(2026,5,1) else '保育期'})

    # B01 (生长期/育肥期: 181-540天)
    for _ in range(12):
        d = date(2025, random.randint(6, 12), random.randint(1, 28))
        cattle_data.append({'pen': 'B01', 'breed': random.choice(cattle_breeds), 'gender': random.choice(['公','母']), 'birth': d, 'source': random.choice(['自繁','外购']), 'stage': '生长期' if d > date(2025,8,1) else '育肥期'})

    # B02
    for _ in range(6):
        d = date(2025, random.randint(6, 12), random.randint(1, 28))
        cattle_data.append({'pen': 'B02', 'breed': random.choice(cattle_breeds), 'gender': random.choice(['公','母']), 'birth': d, 'source': random.choice(['自繁','外购']), 'stage': '生长期'})

    # B03
    for _ in range(3):
        d = date(2025, random.randint(6, 12), random.randint(1, 28))
        cattle_data.append({'pen': 'B03', 'breed': random.choice(cattle_breeds), 'gender': random.choice(['公','母']), 'birth': d, 'source': random.choice(['自繁','外购']), 'stage': '育肥期'})

    # C01 (繁育期, 母)
    for _ in range(4):
        d = date(2024, random.randint(1, 12), random.randint(1, 28))
        cattle_data.append({'pen': 'C01', 'breed': random.choice(cattle_breeds), 'gender': '母', 'birth': d, 'source': '自繁', 'stage': '繁育期'})

    # C02
    for _ in range(2):
        d = date(2024, random.randint(1, 12), random.randint(1, 28))
        cattle_data.append({'pen': 'C02', 'breed': random.choice(cattle_breeds), 'gender': '母', 'birth': d, 'source': '自繁', 'stage': '繁育期'})

    # D01 (种公牛)
    cattle_data.append({'pen': 'D01', 'breed': '西门塔尔牛', 'gender': '公', 'birth': date(2023, 3, 15), 'source': '外购', 'stage': '种用'})

    # ===== 创建牛的档案 =====
    for cd in cattle_data:
        pen_code = cd['pen']
        ear_tag = next_tag(pen_code)
        pen_id = pen_map[pen_code]
        animals.append(Animal(
            farm_id=1, ear_tag=ear_tag, species='牛', breed=cd['breed'],
            pen_id=pen_id, gender=cd['gender'], birth_date=cd['birth'],
            in_date=cd['birth'] + timedelta(days=random.randint(3, 30)),
            growth_stage=cd['stage'], status='在栏', source=cd['source'],
            remark=None,
        ))

    # ===== 羊的档案 (部分圈舍) =====
    sheep_data = []
    # A01 放几只羔羊
    for _ in range(3):
        d = date(2026, random.randint(6, 8), random.randint(1, 28))
        sheep_data.append({'pen': 'A01', 'breed': random.choice(sheep_breeds), 'gender': random.choice(['公','母']), 'birth': d, 'stage': '羔羊期'})
    # B02
    for _ in range(4):
        d = date(2026, random.randint(1, 5), random.randint(1, 28))
        sheep_data.append({'pen': 'B02', 'breed': random.choice(sheep_breeds), 'gender': random.choice(['公','母']), 'birth': d, 'stage': '生长期'})
    # C02
    for _ in range(2):
        d = date(2025, random.randint(1, 12), random.randint(1, 28))
        sheep_data.append({'pen': 'C02', 'breed': random.choice(sheep_breeds), 'gender': '母', 'birth': d, 'stage': '繁育期'})

    for sd in sheep_data:
        ear_tag = next_tag(sd['pen'])
        pen_code = sd['pen']
        animals.append(Animal(
            farm_id=1, ear_tag=ear_tag, species='羊', breed=sd['breed'],
            pen_id=pen_map[pen_code], gender=sd['gender'], birth_date=sd['birth'],
            in_date=sd['birth'] + timedelta(days=random.randint(3, 15)),
            growth_stage=sd['stage'], status='在栏', source='自繁',
            remark=None,
        ))

    # ===== 猪的档案 =====
    pig_data = []
    for _ in range(5):
        d = date(2026, random.randint(5, 8), random.randint(1, 28))
        pig_data.append({'pen': 'A02', 'breed': random.choice(pig_breeds), 'gender': random.choice(['公','母']), 'birth': d, 'stage': '仔猪期' if d > date(2026,7,1) else '保育期'})
    for _ in range(6):
        d = date(2026, random.randint(2, 6), random.randint(1, 28))
        pig_data.append({'pen': 'B03', 'breed': random.choice(pig_breeds), 'gender': random.choice(['公','母']), 'birth': d, 'stage': '生长期'})

    for pd in pig_data:
        ear_tag = next_tag(pd['pen'])
        pen_code = pd['pen']
        animals.append(Animal(
            farm_id=1, ear_tag=ear_tag, species='猪', breed=pd['breed'],
            pen_id=pen_map[pen_code], gender=pd['gender'], birth_date=pd['birth'],
            in_date=pd['birth'] + timedelta(days=random.randint(3, 20)),
            growth_stage=pd['stage'], status='在栏', source='外购',
            remark=None,
        ))

    # 添加几条已出栏的记录
    for i in range(5):
        animals.append(Animal(
            farm_id=1, ear_tag=f'200{i+1}', species='牛', breed=random.choice(cattle_breeds),
            pen_id=None, gender=random.choice(['公','母']),
            birth_date=date(2024, random.randint(1,6), 1),
            in_date=date(2024, random.randint(3,8), 1),
            out_date=date(2026, random.randint(1,7), 1),
            growth_stage='育肥期', status='已出栏', source='外购',
            remark='已出栏销售',
        ))

    # 写入数据库
    db.add_all(animals)
    db.commit()

    # 更新圈舍存栏数
    from sqlalchemy import func
    pen_counts = db.query(Animal.pen_id, func.count(Animal.id)).filter(Animal.status == '在栏').group_by(Animal.pen_id).all()
    for pen_id, cnt in pen_counts:
        db.query(Pen).filter(Pen.id == pen_id).update({'current_count': cnt})
    db.commit()

    # 统计信息
    total = db.query(Animal).filter(Animal.deleted == False).count()
    in_pen = db.query(Animal).filter(Animal.status == '在栏').count()
    sold = db.query(Animal).filter(Animal.status == '已出栏').count()
    pens_info = db.query(Pen).all()

    print(f"=== 数据生成完成 ===")
    print(f"畜禽总数: {total}")
    print(f"在栏数:   {in_pen}")
    print(f"已出栏:   {sold}")
    print(f"\n圈舍概况:")
    for p in pens_info:
        print(f"  {p.pen_code} ({p.pen_type}类) - 容量:{p.capacity} 存栏:{p.current_count}")
    print(f"\n品种分布:")
    from sqlalchemy import func
    breeds = db.query(Animal.species, Animal.breed, func.count(Animal.id)).filter(Animal.deleted == False).group_by(Animal.species, Animal.breed).all()
    for sp, br, cnt in breeds:
        print(f"  {sp} - {br}: {cnt}只")

finally:
    db.close()
