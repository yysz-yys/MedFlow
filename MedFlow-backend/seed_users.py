"""
重置用户/医生/病人数据：
- 仅保留3个指定用户，其余全删
- 补充到50人：1管理员 + 15医生 + 34病人
- ID从1开始连续，复用被删除的ID
运行方式: cd MedFlow-backend && python seed_users.py
"""
from sqlalchemy import create_engine, text
from app.core.config import get_settings
from app.core.security import hash_password
import random

settings = get_settings()
engine = create_engine(settings.database_url_sync, echo=False)
PWD = "doctordefault"

# ── 保留的用户 ──────────────────────────────────────────
KEEP_EMAILS = {
    "admin@medflow.com",      # 管理员
    "doctor1@medflow.com",    # 医生
    "hmklo@nomi.edu.kg",      # 病人
}

# ── 新增医生 (14 人) ─────────────────────────────────────
DOCTORS = [
    ("李建国",  "doctor2@medflow.com",   2,  "主任医师",   "擅长呼吸系统感染性疾病及肺部肿瘤的综合诊治，从医30余年"),
    ("王秀英",  "doctor3@medflow.com",   3,  "副主任医师", "消化内镜诊断与治疗专家，擅长早期胃癌筛查及内镜下微创治疗"),
    ("刘志强",  "doctor4@medflow.com",   4,  "主任医师",   "脑血管疾病及帕金森病的诊治，神经介入治疗经验丰富"),
    ("陈美玲",  "doctor5@medflow.com",  12,  "副主任医师", "关节外科与运动医学，擅长髋膝关节置换及关节镜微创手术"),
    ("赵永刚",  "doctor6@medflow.com",  11,  "主任医师",   "肝胆胰外科及胃肠肿瘤的腹腔镜微创手术，年手术量超500台"),
    ("周丽华",  "doctor7@medflow.com",  18,  "主任医师",   "高危妊娠管理及妇科肿瘤诊治，擅长宫腹腔镜联合手术"),
    ("吴明辉",  "doctor8@medflow.com",  19,  "副主任医师", "儿童呼吸系统疾病及新生儿危重症救治，深耕儿科20年"),
    ("郑海龙",  "doctor9@medflow.com",  13,  "主任医师",   "泌尿系肿瘤及结石的微创治疗，经皮肾镜及输尿管软镜技术"),
    ("孙晓芳",  "doctor10@medflow.com", 21,  "副主任医师", "眼底病及青光眼的诊治，擅长白内障超声乳化及玻璃体切割手术"),
    ("马国强",  "doctor11@medflow.com", 28,  "副主任医师", "急危重症抢救，擅长心肺复苏、中毒及多发伤的急诊处置"),
    ("黄丽萍",  "doctor12@medflow.com", 24,  "主治医师",   "变态反应性皮肤病及自身免疫性皮肤病的诊治"),
    ("林志远",  "doctor13@medflow.com", 26,  "主任医师",   "中医内科疑难杂症，擅长心脑血管疾病及脾胃病的中医药治疗"),
    ("何雪梅",  "doctor14@medflow.com",  6,  "副主任医师", "糖尿病及甲状腺疾病的个体化治疗，在垂体肾上腺疾病方面有丰富经验"),
    ("罗文斌",  "doctor15@medflow.com",  9,  "主任医师",   "肿瘤靶向治疗及免疫治疗，晚期肿瘤的综合治疗策略制定"),
]

# ── 新增病人 (33 人，1个已有) ──────────────────────────────
PATIENTS = [
    ("王建国", "patient1@medflow.com",  1, "1965-03-15", "北京市朝阳区望京西园三区12号楼",   "A",  "无"),
    ("李秀兰", "patient2@medflow.com",  2, "1972-08-22", "北京市海淀区中关村南大街5号院",     "B",  "青霉素过敏"),
    ("张明辉", "patient3@medflow.com",  1, "1980-11-05", "上海市浦东新区张江高科技园区碧波路", "O",  "无"),
    ("陈丽华", "patient4@medflow.com",  2, "1992-06-18", "广州市天河区体育西路维多利广场",     "AB", "磺胺类药物过敏"),
    ("赵永强", "patient5@medflow.com",  1, "1958-01-30", "成都市武侯区科华北路143号",          "A",  "无"),
    ("孙晓红", "patient6@medflow.com",  2, "1985-04-12", "武汉市洪山区珞喻路1037号",           "B",  "花粉过敏"),
    ("周志伟", "patient7@medflow.com",  1, "1976-09-08", "南京市鼓楼区汉口路22号",             "O",  "无"),
    ("吴玉兰", "patient8@medflow.com",  2, "1963-12-25", "西安市雁塔区太白南路2号",            "A",  "无"),
    ("郑国强", "patient9@medflow.com",  1, "1990-07-14", "杭州市西湖区浙大路38号",             "B",  "海鲜过敏"),
    ("王桂英", "patient10@medflow.com", 2, "1955-05-20", "重庆市渝中区长江二路174号",          "O",  "无"),
    ("冯志明", "patient11@medflow.com", 1, "1988-02-28", "深圳市南山区科技园南区",             "AB", "无"),
    ("褚丽娟", "patient12@medflow.com", 2, "1970-10-01", "天津市和平区南京路183号",            "A",  "头孢过敏"),
    ("蒋永康", "patient13@medflow.com", 1, "1968-07-04", "苏州市姑苏区干将东路178号",          "B",  "无"),
    ("沈秀珍", "patient14@medflow.com", 2, "1982-03-21", "长沙市岳麓区麓山南路932号",          "O",  "无"),
    ("韩志勇", "patient15@medflow.com", 1, "1995-11-11", "济南市历下区文化西路44号",           "A",  "酒精过敏"),
    ("杨丽华", "patient16@medflow.com", 2, "1960-08-16", "郑州市金水区农业路63号",             "B",  "无"),
    ("朱伟民", "patient17@medflow.com", 1, "1978-01-09", "青岛市市南区香港中路10号",           "O",  "无"),
    ("秦小英", "patient18@medflow.com", 2, "1993-06-30", "大连市沙河口区黄河路794号",          "AB", "无"),
    ("许建华", "patient19@medflow.com", 1, "1957-04-17", "厦门市思明区思明南路422号",          "A",  "阿司匹林过敏"),
    ("尤美琴", "patient20@medflow.com", 2, "1986-09-25", "福州市鼓楼区东街口百货大楼",         "B",  "无"),
    ("何志刚", "patient21@medflow.com", 1, "1962-12-03", "合肥市蜀山区长江西路130号",          "O",  "无"),
    ("吕桂芳", "patient22@medflow.com", 2, "1974-05-08", "无锡市滨湖区太湖大道188号",          "A",  "牛奶过敏"),
    ("施永平", "patient23@medflow.com", 1, "1991-08-19", "东莞市南城区会展北路",               "B",  "无"),
    ("张雪梅", "patient24@medflow.com", 2, "1967-01-26", "昆明市五华区翠湖南路6号",            "O",  "无"),
    ("孔令辉", "patient25@medflow.com", 1, "1983-10-14", "哈尔滨市南岗区西大直街92号",         "A",  "无花果过敏"),
    ("曹玉珍", "patient26@medflow.com", 2, "1959-07-07", "沈阳市和平区文化路3号",              "AB", "无"),
    ("严大伟", "patient27@medflow.com", 1, "1971-02-22", "太原市小店区坞城路92号",             "B",  "碘造影剂过敏"),
    ("华秀英", "patient28@medflow.com", 2, "1989-12-18", "南昌市东湖区八一大道128号",          "O",  "无"),
    ("金志豪", "patient29@medflow.com", 1, "1964-06-05", "贵阳市云岩区北京路9号",              "A",  "无"),
    ("魏小红", "patient30@medflow.com", 2, "1977-09-13", "南宁市青秀区民族大道100号",          "B",  "猫毛过敏"),
    ("陶建平", "patient31@medflow.com", 1, "1994-03-28", "长春市朝阳区前进大街2699号",         "O",  "无"),
    ("姜翠花", "patient32@medflow.com", 2, "1961-11-02", "兰州市城关区天水南路222号",          "A",  "无"),
    ("谢远航", "patient33@medflow.com", 1, "1987-08-09", "乌鲁木齐市天山区解放南路358号",     "AB", "无"),
]

# ── 原来的三条记录需要重新插入的密码 ─────────────────────
KEEP_USERS_PASSWORD = {
    "admin@medflow.com":   "medflowadmin",
    "doctor1@medflow.com": "doctordefault",
    "hmklo@nomi.edu.kg":   "123456",
}
KEEP_DOCTORS = {
    # email → (name, dept_id, title, intro)
    "doctor1@medflow.com": ("张伟华", 1, "主治医师", "心血管内科常见病及冠脉介入治疗的临床与科研工作"),
}
KEEP_PATIENTS = {
    "hmklo@nomi.edu.kg": (1, "1988-05-15", "广东省深圳市南山区科技园", "O", "无"),
}
KEEP_ADMINS = {
    "admin@medflow.com": "系统管理员",
}

with engine.connect() as conn:
    cx = conn  # alias

    # ── 0. 查当前数据 ──
    old_users = cx.execute(text("SELECT id, email, name, role FROM user ORDER BY id")).fetchall()
    print(f"当前用户 ({len(old_users)}人):")
    for u in old_users:
        print(f"  {u[0]:3d} | {u[1]:30s} | {u[2]:8s} | role={u[3]}")
    print()

    # ── 1. 关闭FK检查，全清 ──
    cx.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

    for tbl in ["appointment", "diagnosis_record", "prescription", "schedule",
                "notification", "audit_log", "order_record"]:
        try:
            cnt = cx.execute(text(f"DELETE FROM {tbl}")).rowcount
            if cnt: print(f"  清理 {tbl}: {cnt} 行")
        except Exception: pass

    del_doc = cx.execute(text("DELETE FROM doctor")).rowcount
    del_pat = cx.execute(text("DELETE FROM patient")).rowcount
    del_usr = cx.execute(text("DELETE FROM user")).rowcount
    print(f"\n全清: doctor {del_doc}行, patient {del_pat}行, user {del_usr}行")

    # ── 2. 重置所有自增 ──
    for tbl in ["user", "doctor", "patient", "appointment", "diagnosis_record",
                "prescription", "schedule", "notification"]:
        try:
            cx.execute(text(f"ALTER TABLE {tbl} AUTO_INCREMENT = 1"))
        except Exception:
            pass

    cx.commit()
    print("已重置所有自增ID")

    # ── 3. 重新插入：先admin → 再医生 → 再病人 ──
    user_seq = 0

    # 3a. 管理员 (1人)
    user_seq += 1
    for email, name in KEEP_ADMINS.items():
        pw = KEEP_USERS_PASSWORD[email]
        cx.execute(text(
            "INSERT INTO user (id, email, password, name, role, created_at, updated_at) VALUES (:id, :e, :p, :n, 0, NOW(), NOW())"
        ), {"id": user_seq, "e": email, "p": hash_password(pw), "n": name})
        print(f"  user {user_seq}: {name} ({email}) [admin]")

    # 3b. 医生 (15人)
    # 先处理保留的医生
    doc_email = "doctor1@medflow.com"
    user_seq += 1
    name, dept_id, title, intro = KEEP_DOCTORS[doc_email]
    pw = KEEP_USERS_PASSWORD[doc_email]
    cx.execute(text(
        "INSERT INTO user (id, email, password, name, role, created_at, updated_at) VALUES (:id, :e, :p, :n, 1, NOW(), NOW())"
    ), {"id": user_seq, "e": doc_email, "p": hash_password(pw), "n": name})
    cx.execute(text(
        "INSERT INTO doctor (id, user_id, department_id, title, introduction, created_at, updated_at) VALUES (:id, :uid, :did, :t, :i, NOW(), NOW())"
    ), {"id": user_seq - 1, "uid": user_seq, "did": dept_id, "t": title, "i": intro})
    print(f"  user {user_seq}: {name} ({doc_email}) [doctor] -> {dept_id}.{title}")

    # 新增14个医生
    for name, email, dept_id, title, intro in DOCTORS:
        user_seq += 1
        cx.execute(text(
            "INSERT INTO user (id, email, password, name, role, created_at, updated_at) VALUES (:id, :e, :p, :n, 1, NOW(), NOW())"
        ), {"id": user_seq, "e": email, "p": hash_password(PWD), "n": name})
        cx.execute(text(
            "INSERT INTO doctor (id, user_id, department_id, title, introduction, created_at, updated_at) VALUES (:id, :uid, :did, :t, :i, NOW(), NOW())"
        ), {"id": user_seq - 1, "uid": user_seq, "did": dept_id, "t": title, "i": intro})
        print(f"  user {user_seq}: {name} ({email}) [doctor] -> {dept_id}.{title}")

    # 3c. 病人 (34人)
    # 先处理保留的病人
    pat_email = "hmklo@nomi.edu.kg"
    user_seq += 1
    gender, birth, addr, blood, allergy = KEEP_PATIENTS[pat_email]
    pw = KEEP_USERS_PASSWORD[pat_email]
    cx.execute(text(
        "INSERT INTO user (id, email, password, name, role, created_at, updated_at) VALUES (:id, :e, :p, :n, 2, NOW(), NOW())"
    ), {"id": user_seq, "e": pat_email, "p": hash_password(pw), "n": "hmklo"})
    cx.execute(text(
        "INSERT INTO patient (id, user_id, gender, birth_date, address, blood_type, allergy_history, created_at, updated_at) "
        "VALUES (:id, :uid, :g, :b, :a, :bt, :ah, NOW(), NOW())"
    ), {"id": user_seq - 16, "uid": user_seq, "g": gender, "b": birth, "a": addr, "bt": blood, "ah": allergy})
    print(f"  user {user_seq}: hmklo ({pat_email}) [patient]")

    # 新增33个病人
    for name, email, gender, birth, addr, blood, allergy in PATIENTS:
        user_seq += 1
        cx.execute(text(
            "INSERT INTO user (id, email, password, name, role, created_at, updated_at) VALUES (:id, :e, :p, :n, 2, NOW(), NOW())"
        ), {"id": user_seq, "e": email, "p": hash_password("123456"), "n": name})
        cx.execute(text(
            "INSERT INTO patient (id, user_id, gender, birth_date, address, blood_type, allergy_history, created_at, updated_at) "
            "VALUES (:id, :uid, :g, :b, :a, :bt, :ah, NOW(), NOW())"
        ), {"id": user_seq - 16, "uid": user_seq, "g": gender, "b": birth, "a": addr, "bt": blood, "ah": allergy})
        print(f"  user {user_seq}: {name} ({email}) [patient]")

    # ── 4. 恢复FK检查 ──
    cx.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    cx.commit()

    print(f"\n✅ 完成! 总计 {user_seq} 用户 (1管理员 + 15医生 + {user_seq - 16}病人)")

# ── 5. 验证 ──
with engine.connect() as conn:
    print("\n==================== 验证 ====================")
    for role, label in [(0, "管理员"), (1, "医生"), (2, "病人")]:
        rows = conn.execute(text(
            "SELECT id, name, email FROM user WHERE role=:r ORDER BY id"
        ), {"r": role}).fetchall()
        print(f"\n{label} ({len(rows)}人):")
        for r in rows:
            print(f"  {r[0]:3d}. {r[1]:8s} {r[2]}")

    dc = conn.execute(text("SELECT count(*) FROM doctor")).scalar()
    pc = conn.execute(text("SELECT count(*) FROM patient")).scalar()
    uc = conn.execute(text("SELECT count(*) FROM user")).scalar()
    print(f"\n总计: user={uc}, doctor={dc}, patient={pc}")
