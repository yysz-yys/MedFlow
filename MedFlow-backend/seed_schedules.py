"""
为所有医生生成未来两周真实排班数据。
运行方式: cd MedFlow-backend && python seed_schedules.py
"""
from sqlalchemy import create_engine, text
from app.core.config import get_settings
from datetime import date, timedelta

settings = get_settings()
engine = create_engine(settings.database_url_sync, echo=False)

# 时段定义
SLOTS = {
    "上午": ("08:00", "12:00", 20),
    "下午": ("14:00", "17:00", 15),
    "夜间": ("18:00", "21:00", 10),
}

# 医生排班计划 (doctor_id, [(weekday, slot_key), ...])
# weekday: 0=周一 1=周二 2=周三 3=周四 4=周五 5=周六 6=周日
SCHEDULE_PLAN = {
    # 1. 张伟华 - 心血管内科 主治医师 (周一三四五上午 + 周三下午)
    1: [("上午", [0, 2, 3, 4]), ("下午", [2])],
    # 2. 李建国 - 呼吸内科 主任医师 (周一二四上午)
    2: [("上午", [0, 1, 3])],
    # 3. 王秀英 - 消化内科 副主任医师 (周一三五上午 + 周二四下午)
    3: [("上午", [0, 2, 4]), ("下午", [1, 3])],
    # 4. 刘志强 - 神经内科 主任医师 (周二四上午 + 周一三下午)
    4: [("上午", [1, 3]), ("下午", [0, 2])],
    # 5. 陈美玲 - 骨科 副主任医师 (周一三上午 + 周四五下午)
    5: [("上午", [0, 2]), ("下午", [3, 4])],
    # 6. 赵永刚 - 普外科 主任医师 (周一二三五上午)
    6: [("上午", [0, 1, 2, 4])],
    # 7. 周丽华 - 妇产科 主任医师 (周一三五上午 + 周二四下午)
    7: [("上午", [0, 2, 4]), ("下午", [1, 3])],
    # 8. 吴明辉 - 儿科 副主任医师 (周一至五上午)
    8: [("上午", [0, 1, 2, 3, 4])],
    # 9. 郑海龙 - 泌尿外科 主任医师 (周二四上午 + 周一下午)
    9: [("上午", [1, 3]), ("下午", [0])],
    # 10. 孙晓芳 - 眼科 副主任医师 (周一二三上午 + 周四五下午)
    10: [("上午", [0, 1, 2]), ("下午", [3, 4])],
    # 11. 马国强 - 急诊科 副主任医师 (急诊科不休，周一至日都有)
    11: [("上午", [0,1,2,3,4,5,6]), ("下午", [0,1,2,3,4,5,6]), ("夜间", [0,1,2,3,4,5,6])],
    # 12. 黄丽萍 - 皮肤科 主治医师 (周一至五上午 + 一三五下午)
    12: [("上午", [0, 1, 2, 3, 4]), ("下午", [0, 2, 4])],
    # 13. 林志远 - 中医科 主任医师 (周一二三五上午)
    13: [("上午", [0, 1, 2, 4])],
    # 14. 何雪梅 - 内分泌科 副主任医师 (周一二四上午 + 周三下午)
    14: [("上午", [0, 1, 3]), ("下午", [2])],
    # 15. 罗文斌 - 肿瘤内科 主任医师 (周一三四五上午)
    15: [("上午", [0, 2, 3, 4])],
}

# 未来两周的起始日期（从下周一算）
today = date.today()
days_until_monday = (7 - today.weekday()) % 7
if days_until_monday == 0:
    days_until_monday = 0  # 今天就是周一
monday = today + timedelta(days=days_until_monday)

print(f"今天: {today} (周{today.weekday()+1})")
print(f"排班起始周一: {monday}")
print(f"排班范围: {monday} ~ {monday + timedelta(days=13)}")

with engine.connect() as conn:
    cx = conn

    # 清理多余医生（超出15个的）
    extra_docs = cx.execute(text(
        "SELECT d.id, u.id FROM doctor d JOIN user u ON d.user_id=u.id WHERE d.id > 15"
    )).fetchall()
    if extra_docs:
        cx.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for did, uid in extra_docs:
            cx.execute(text("DELETE FROM doctor WHERE id = :id"), {"id": did})
            cx.execute(text("DELETE FROM user WHERE id = :id"), {"id": uid})
        cx.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        cx.commit()
        print(f"清理多余医生: {[(d[0], d[1]) for d in extra_docs]}")

    # 清空旧排班
    cx.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    old = cx.execute(text("DELETE FROM doctor_schedule")).rowcount
    cx.execute(text("ALTER TABLE doctor_schedule AUTO_INCREMENT = 1"))
    cx.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    cx.commit()
    print(f"\n已清空 {old} 条旧排班")

    total = 0
    for doctor_id, slot_plans in SCHEDULE_PLAN.items():
        for slot_key, weekdays in slot_plans:
            start_t, end_t, max_p = SLOTS[slot_key]
            for wd in weekdays:
                # 第一周
                d1 = monday + timedelta(days=wd)
                cx.execute(text(
                    "INSERT INTO doctor_schedule (doctor_id, work_date, start_time, end_time, max_patients, status, created_at, updated_at) "
                    "VALUES (:did, :d, :s, :e, :m, 1, NOW(), NOW())"
                ), {"did": doctor_id, "d": d1, "s": start_t, "e": end_t, "m": max_p})
                total += 1
                # 第二周
                d2 = d1 + timedelta(days=7)
                cx.execute(text(
                    "INSERT INTO doctor_schedule (doctor_id, work_date, start_time, end_time, max_patients, status, created_at, updated_at) "
                    "VALUES (:did, :d, :s, :e, :m, 1, NOW(), NOW())"
                ), {"did": doctor_id, "d": d2, "s": start_t, "e": end_t, "m": max_p})
                total += 1
    cx.commit()

    print(f"已生成 {total} 条排班记录")

# 验证
with engine.connect() as conn:
    stats = conn.execute(text(
        "SELECT u.name, count(*) as cnt, "
        "min(ds.work_date) as from_d, max(ds.work_date) as to_d "
        "FROM doctor_schedule ds "
        "JOIN doctor d ON ds.doctor_id = d.id "
        "JOIN user u ON d.user_id = u.id "
        "GROUP BY ds.doctor_id, u.name ORDER BY ds.doctor_id"
    )).fetchall()

    print(f"\n排班统计 ({len(stats)} 位医生):")
    for s in stats:
        print(f"  {s[0]:6s} | {s[2]} ~ {s[3]} | {s[1]}条")

    total_slots = conn.execute(text("SELECT count(*) FROM doctor_schedule")).scalar()
    print(f"\n总计: {total_slots} 条排班")

    # 按天统计
    day_stats = conn.execute(text(
        "SELECT work_date, count(*) FROM doctor_schedule GROUP BY work_date ORDER BY work_date"
    )).fetchall()
    print(f"\n按天分布:")
    for ds in day_stats:
        wd = ds[0].weekday()
        wd_cn = ['一','二','三','四','五','六','日'][wd]
        print(f"  {ds[0]} (周{wd_cn}): {ds[1]}个时段")
