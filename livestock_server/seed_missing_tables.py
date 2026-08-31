"""
补齐 4 张空表的模拟数据（只 INSERT，不清库、不影响现有数据）：
- breeding_male            公畜健康档案（缺口4 新功能）
- sys_notice               系统公告
- sys_message              站内消息（缺口6 新功能）
- animal_archive_history   档案历史（删除/出栏转入）

用法:
    python seed_missing_tables.py
每张表插入前都会检查是否已有数据，已有则跳过，可重复执行。
"""
import sys
sys.path.insert(0, 'D:/Code/system/livestock_server')

from datetime import date, datetime, timedelta

from app.database import SessionLocal
from app.modules.animal.model import AnimalHistory
from app.modules.breeding.model import BreedingMale
from app.modules.system.model import SysMessage, SysNotice

db = SessionLocal()
try:
    # ===== 1. 公畜健康档案：只给在栏、达到可繁育日龄的公畜建档 =====
    if db.query(BreedingMale).count() == 0:
        males = [
            # farm 4 = 阳光牧场（牛），farm 5 = 八戒牧场（猪）
            dict(farm_id=4, ear_tag='2701', health_status='健康',
                 use_start_date=date(2024, 3, 1),
                 semen_quality='精液活力0.8，密度中等，采精频率每周1次',
                 remark='黄牛种公牛，性情温顺'),
            dict(farm_id=4, ear_tag='2206', health_status='健康',
                 use_start_date=date(2024, 6, 1),
                 semen_quality='精液活力0.85，密度高',
                 remark='西门塔尔牛种公牛，主配本场母牛群'),
            dict(farm_id=4, ear_tag='2202', health_status='亚健康',
                 use_start_date=date(2026, 1, 1),
                 semen_quality='近期精液活力0.6偏低，建议加强运动与营养，两周后复检',
                 remark='安格斯牛，待复检'),
            dict(farm_id=5, ear_tag='3501', health_status='健康',
                 use_start_date=date(2024, 10, 1),
                 semen_quality='精液活力0.8，密度正常',
                 remark='杜洛克种公猪，配种成绩稳定'),
        ]
        db.add_all([BreedingMale(**m) for m in males])
        db.commit()
        print(f'breeding_male: 插入 {len(males)} 条')
    else:
        print('breeding_male 已有数据，跳过')

    # ===== 2. 系统公告 =====
    if db.query(SysNotice).count() == 0:
        notices = [
            dict(notice_title='关于开展秋季动物疫病集中免疫工作的通知',
                 notice_type='通知',
                 notice_content='各养殖场：按照属地动物疫病防控要求，9 月 10 日至 9 月 30 日开展口蹄疫、'
                                '猪瘟、禽流感等集中免疫工作，请各场提前核对免疫档案，配合兽医站完成接种并'
                                '及时在系统中登记疫苗记录。',
                 status=1, create_by='admin'),
            dict(notice_title='智慧养殖平台 V2.4 更新公告',
                 notice_type='公告',
                 notice_content='本次更新内容：1）繁育模块新增公畜健康档案；2）审核结果将通过站内消息推送；'
                                '3）统计报表新增受孕率、生产率、成活率等指标。使用中如有问题请联系管理员。',
                 status=1, create_by='admin'),
            dict(notice_title='暴雨预警：请提前做好圈舍防汛检查',
                 notice_type='通知',
                 notice_content='气象台发布暴雨蓝色预警，预计未来 48 小时有强降雨。请各场检查圈舍屋顶、排水沟，'
                                '备足垫料与应急电源，低洼圈舍提前转移畜禽。',
                 status=1, create_by='admin'),
        ]
        db.add_all([SysNotice(**n) for n in notices])
        db.commit()
        print(f'sys_notice: 插入 {len(notices)} 条')
    else:
        print('sys_notice 已有数据，跳过')

    # ===== 3. 站内消息（收件人取现有真实用户）=====
    # 用户: 19 sunshine(阳光牧场场主) / 24 bajie(八戒牧场场主) / 25 niuniu(牛牛养殖场主)
    if db.query(SysMessage).count() == 0:
        now = datetime.now()
        messages = [
            dict(farm_id=4, receiver_user_id=19, message_type='审核结果',
                 title='饲喂记录审核通过',
                 content='您 8 月 30 日提交的育肥牛舍饲喂记录已通过审核。',
                 related_module='feeding', related_id=1, is_read=0, read_time=None),
            dict(farm_id=4, receiver_user_id=19, message_type='审核结果',
                 title='物资采购单审核退回',
                 content='您提交的「玉米 2 吨」采购单被退回：数量与预算不符，请修改后重新提交。',
                 related_module='purchase', related_id=2, is_read=0, read_time=None),
            dict(farm_id=4, receiver_user_id=19, message_type='系统提醒',
                 title='疫苗加强针到期提醒',
                 content='圈舍 A02 有 8 头犊牛口蹄疫疫苗即将到期，请及时安排补免并登记疫苗记录。',
                 related_module='vaccine', related_id=1, is_read=1,
                 read_time=now - timedelta(days=1, hours=3)),
            dict(farm_id=5, receiver_user_id=24, message_type='审核结果',
                 title='饲喂记录审核通过',
                 content='您 8 月 29 日提交的保育舍饲喂记录已通过审核。',
                 related_module='feeding', related_id=2, is_read=0, read_time=None),
            dict(farm_id=5, receiver_user_id=24, message_type='系统提醒',
                 title='物资库存不足预警',
                 content='「育肥料」当前库存低于安全阈值，请及时采购补库。',
                 related_module='consume', related_id=3, is_read=0, read_time=None),
            dict(farm_id=6, receiver_user_id=25, message_type='审核结果',
                 title='诊疗记录审核通过',
                 content='您提交的 11 号圈舍牛只诊疗记录已通过审核。',
                 related_module='medical', related_id=1, is_read=0, read_time=None),
        ]
        db.add_all([SysMessage(**m) for m in messages])
        db.commit()
        print(f'sys_message: 插入 {len(messages)} 条')
    else:
        print('sys_message 已有数据，跳过')

    # ===== 4. 档案历史（模拟已出栏/死亡后转入的历史档案）=====
    if db.query(AnimalHistory).count() == 0:
        # pen_id 对应真实圈舍：farm4 B02=23 / C01=25，farm5 B01=30，farm6 A01=36
        histories = [
            dict(farm_id=4, ear_tag='2207', species='牛', breed='西门塔尔牛', pen_id=23,
                 gender='公', birth_date=date(2023, 4, 10), in_date=date(2023, 4, 10),
                 out_date=date(2026, 7, 20), growth_stage='育肥期', physio_status=None,
                 status='已出栏', source='自繁', sire_tag=None, dam_tag=None,
                 remark='育肥达标，出栏销售'),
            dict(farm_id=4, ear_tag='1205', species='羊', breed='波尔山羊', pen_id=25,
                 gender='母', birth_date=date(2024, 2, 15), in_date=date(2024, 2, 15),
                 out_date=date(2026, 6, 5), growth_stage='育肥期', physio_status='休情',
                 status='已出栏', source='外购', sire_tag=None, dam_tag=None,
                 remark='体重达标出栏'),
            dict(farm_id=5, ear_tag='3103', species='猪', breed='杜长大三元猪', pen_id=30,
                 gender='公', birth_date=date(2025, 12, 1), in_date=date(2025, 12, 1),
                 out_date=None, growth_stage='保育期', physio_status=None,
                 status='死亡', source='自繁', sire_tag=None, dam_tag=None,
                 remark='2026-05 呼吸道疾病治疗无效死亡，已无害化处理'),
            dict(farm_id=6, ear_tag='4201', species='牛', breed='黄牛', pen_id=36,
                 gender='母', birth_date=date(2022, 8, 20), in_date=date(2022, 8, 20),
                 out_date=date(2026, 4, 12), growth_stage='育肥期', physio_status='淘汰',
                 status='已出栏', source='外购', sire_tag=None, dam_tag=None,
                 remark='老龄母牛淘汰出栏'),
        ]
        db.add_all([AnimalHistory(**h) for h in histories])
        db.commit()
        print(f'animal_archive_history: 插入 {len(histories)} 条')
    else:
        print('animal_archive_history 已有数据，跳过')
finally:
    db.close()

print('完成。')
