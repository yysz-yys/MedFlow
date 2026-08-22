"""
为过去7天生成预约数据，让工作台图表有数据可展示。
如果没有过去7天的排班，会自动先生成排班再生成预约。
运行方式: cd MedFlow-backend && python seed_appointments.py
"""
from sqlalchemy import create_engine, text
from app.core.config import get_settings
from datetime import date, timedelta, datetime
import random

settings = get_settings()
engine = create_engine(settings.database_url_sync, echo=False)
random.seed(42)

today = date.today()
start = today - timedelta(days=6)  # 过去7天（含今天）

# 时段定义（与 seed_schedules.py 保持一致）
SLOTS = {"上午": ("08:00", "12:00", 20), "下午": ("14:00", "17:00", 15), "夜间": ("18:00", "21:00", 10)}
# 医生排班计划 (doctor_id, [(slot_key, [weekday, ...]), ...])  weekday: 0=周一~6=周日
SCHEDULE_PLAN = {
    1:  [("上午",[0,2,3,4]), ("下午",[2])],
    2:  [("上午",[0,1,3])],
    3:  [("上午",[0,2,4]), ("下午",[1,3])],
    4:  [("上午",[1,3]), ("下午",[0,2])],
    5:  [("上午",[0,2]), ("下午",[3,4])],
    6:  [("上午",[0,1,2,4])],
    7:  [("上午",[0,2,4]), ("下午",[1,3])],
    8:  [("上午",[0,1,2,3,4])],
    9:  [("上午",[1,3]), ("下午",[0])],
    10: [("上午",[0,1,2]), ("下午",[3,4])],
    11: [("上午",[0,1,2,3,4,5,6]), ("下午",[0,1,2,3,4,5,6]), ("夜间",[0,1,2,3,4,5,6])],
    12: [("上午",[0,1,2,3,4]), ("下午",[0,2,4])],
    13: [("上午",[0,1,2,4])],
    14: [("上午",[0,1,3]), ("下午",[2])],
    15: [("上午",[0,2,3,4])],
}

with engine.connect() as conn:
    # 清空旧预约
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    old = conn.execute(text("DELETE FROM appointment")).rowcount
    conn.execute(text("ALTER TABLE appointment AUTO_INCREMENT = 1"))
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    conn.commit()
    print(f"已清空 {old} 条旧预约")

    # 检查过去7天是否有排班，没有则自动生成
    existing = conn.execute(text(
        "SELECT COUNT(*) FROM doctor_schedule "
        "WHERE work_date BETWEEN :start AND :today AND doctor_id > 0"
    ), {"start": start, "today": today}).scalar()

    if existing == 0:
        print("过去7天无排班，自动生成中...")
        gen_total = 0
        for doctor_id, slot_plans in SCHEDULE_PLAN.items():
            for slot_key, weekdays in slot_plans:
                start_t, end_t, max_p = SLOTS[slot_key]
                for wd in weekdays:
                    d = start + timedelta(days=(wd - start.weekday()) % 7)
                    if d > today:
                        continue
                    conn.execute(text(
                        "INSERT INTO doctor_schedule (doctor_id, work_date, start_time, end_time, max_patients, status, created_at, updated_at) "
                        "VALUES (:did, :d, :s, :e, :m, 1, NOW(), NOW())"
                    ), {"did": doctor_id, "d": d, "s": start_t, "e": end_t, "m": max_p})
                    gen_total += 1
        conn.commit()
        print(f"已生成 {gen_total} 条过去7天排班")

    # 获取所有排班（过去7天）
    schedules = conn.execute(text(
        "SELECT ds.id, ds.doctor_id, ds.work_date, ds.start_time, "
        "d.department_id "
        "FROM doctor_schedule ds "
        "JOIN doctor d ON ds.doctor_id = d.id "
        "WHERE ds.work_date BETWEEN :start AND :today "
        "AND ds.doctor_id > 0 "
        "ORDER BY ds.work_date, ds.start_time"
    ), {"start": start, "today": today}).fetchall()

    print(f"过去7天共有 {len(schedules)} 个排班时段")

    # 获取所有病人ID
    patients = [r[0] for r in conn.execute(text(
        "SELECT id FROM patient WHERE deleted_at IS NULL"
    )).fetchall()]
    print(f"可用病人: {len(patients)} 人")

    if not schedules or not patients:
        print("没有排班或病人数据，无法生成预约。请先运行 seed_users.py 和 seed_schedules.py")
        exit(1)

    total = 0
    for s in schedules:
        sched_id, doctor_id, work_date, start_time, dept_id = s

        # 每个时段随机生成 0~3 个预约
        n = random.choices([0, 1, 2, 3], weights=[3, 5, 5, 2])[0]
        for _ in range(n):
            patient_id = random.choice(patients)
            if work_date < today and random.random() < 0.3:
                status = 2
            else:
                status = 1

            # start_time 可能是 timedelta（MySQL TIME 列），统一转成小时
            start_hour = start_time.seconds // 3600 if hasattr(start_time, 'seconds') else start_time.hour
            hour = start_hour + random.randint(0, 3)
            minute = random.choice([0, 15, 30, 45])
            apt_time = datetime.combine(work_date, datetime.min.time()).replace(
                hour=min(hour, start_hour + 3), minute=minute
            )

            conn.execute(text(
                "INSERT INTO appointment "
                "(patient_id, doctor_id, department_id, appointment_time, status, created_at, updated_at) "
                "VALUES (:pid, :did, :dept, :apt, :st, :apt, :apt)"
            ), {
                "pid": patient_id, "did": doctor_id, "dept": dept_id,
                "apt": apt_time, "st": status
            })
            total += 1

    conn.commit()
    print(f"已生成 {total} 条预约")

# 验证
with engine.connect() as conn:
    # 每日统计
    daily = conn.execute(text(
        "SELECT DATE(appointment_time), COUNT(*) "
        "FROM appointment "
        "WHERE appointment_time BETWEEN :start AND :today + INTERVAL 1 DAY "
        "GROUP BY DATE(appointment_time) ORDER BY 1"
    ), {"start": start, "today": today}).fetchall()
    print(f"\n每日预约:")
    for d in daily:
        print(f"  {d[0]}: {d[1]}条")

    # 科室统计
    dept = conn.execute(text(
        "SELECT dept.name, COUNT(*) as cnt "
        "FROM appointment a "
        "JOIN department dept ON a.department_id = dept.id "
        "WHERE DATE(a.appointment_time) = :today "
        "GROUP BY dept.name ORDER BY cnt DESC LIMIT 12"
    ), {"today": today}).fetchall()
    print(f"\n今日科室分布 (Top 12):")
    for d in dept:
        print(f"  {d[0]}: {d[1]}条")

    total = conn.execute(text("SELECT COUNT(*) FROM appointment")).scalar()
    print(f"\n总计: {total} 条预约")
