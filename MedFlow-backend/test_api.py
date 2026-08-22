"""
MedFlow API 全接口测试脚本（从头开始，自动清理）
用法: venv/Scripts/python.exe test_api.py [a|i|模块名...]
     a = 全部自动测试（默认）
     i = 逐步选择，每个接口 y=测 n=跳过 q=退出
     auth departments drugs = 只测指定模块
"""

import requests, json, sys, subprocess, time

BASE = "http://localhost:8001"
PATIENT_EMAIL = "knc8t@yangs.edu.kg"
ADMIN_EMAIL   = "19070924661@163.com"
DOCTOR_EMAIL  = "3575771702@qq.com"
PASS          = "Test123456"
ADMIN_PASS    = "Admin123456"

INTERACTIVE = False  # 是否逐步选择模式

MODULES = {
    "auth":       "认证（7接口）",
    "users":      "用户管理（4接口）",
    "departments":"科室（4接口）",
    "doctors":    "医生（4接口）",
    "schedules":  "排班（4接口）",
    "patients":   "病人（4接口）",
    "drugs":      "药品（5接口）",
    "appointments":"挂号（5接口）",
    "diagnosis":  "诊断（4接口）",
    "prescriptions":"处方+订单（6接口）",
    "files":      "文件（3接口）",
    "notifications":"通知（3接口）",
    "data_dict":  "数据字典（4接口）",
    "sys_config": "系统配置（4接口）",
    "audit_logs": "操作日志（1接口）",
}

ok = 0; fail = 0; skip = 0

def test(name, method, path, expected_status=200, **kwargs):
    global ok, fail, skip
    if INTERACTIVE:
        ans = input(f"  ⏳ 测试 [{name}]? (y=测 / n=跳过 / q=退出): ").strip().lower()
        if ans == "q":
            print("\n  🛑 用户退出测试")
            print_total()
            sys.exit(0)
        if ans == "n":
            skip += 1
            print(f"  ⏭️  跳过 {name}")
            return None
    url = f"{BASE}{path}"
    try:
        r = method(url, **kwargs)
        if r.status_code == expected_status:
            ok += 1; print(f"  ✅ [{r.status_code}] {name}")
        else:
            fail += 1; print(f"  ❌ [{r.status_code}] {name} (expected {expected_status})")
            try: print(f"      Response: {r.json()}")
            except: print(f"      Response: {r.text[:200]}")
        return r
    except Exception as e:
        fail += 1; print(f"  ❌ [ERR] {name}: {e}")
        return None

def print_total():
    total = ok + fail + skip
    print("\n" + "=" * 60)
    if skip > 0:
        print(f"测试完成: 执行{total}个, ✅ {ok} 通过, ❌ {fail} 失败, ⏭️ {skip} 跳过")
    else:
        print(f"测试完成: {total} 个, ✅ {ok} 通过, ❌ {fail} 失败")
    print("=" * 60)
    print("用法: test_api.py [a|i|模块...]  a=自动全部  i=逐步选择")
    print("模块: " + " ".join(MODULES.keys()))

def input_code():
    return input("  >>> 请输入邮箱收到的验证码（6位数字）: ").strip()

def should_run(name):
    return len(sys.argv) == 1 or name in sys.argv

def cleanup_db():
    print("🧹 清理+初始化数据库...")
    try:
        import pymysql
        conn = pymysql.connect(host="127.0.0.1", user="root", password="root", database="medflow")
        cur = conn.cursor()
        tables = ["prescription_item", "drug_order", "prescription",
                  "diagnosis_record", "appointment",
                  "file_attachment", "notification", "doctor_schedule",
                  "patient", "doctor", "user", "verification_code"]
        for t in tables:
            cur.execute(f"DELETE FROM {t}")
        cur.execute("DELETE FROM data_dict WHERE dict_type='test_type'")
        cur.execute("DELETE FROM system_config WHERE config_key='test_config'")
        from app.core.security import hash_password
        admin_hash = hash_password(ADMIN_PASS)
        cur.execute(
            "INSERT INTO `user` (id,password,name,email,role,status,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,NOW(),NOW()) ON DUPLICATE KEY UPDATE password=%s",
            (1, admin_hash, "管理员", ADMIN_EMAIL, 0, 1, admin_hash))
        conn.commit()
        conn.close()
        print("  ✅ 清理完成，管理员账号已初始化（字典和系统配置未动）")
    except Exception as e:
        print(f"  ⚠️ 清理跳过 ({e})")

# ============================================================
print("=" * 60)
print("MedFlow API 全接口测试")
print(f"服务地址: {BASE}")
if len(sys.argv) > 1:
    print(f"测试模块: {', '.join(sys.argv[1:])}")
else:
    print("测试模式: 全部")
print("=" * 60)

# 模式选择
if len(sys.argv) > 1 and sys.argv[1] == "i":
    INTERACTIVE = True
    sys.argv.pop(1)  # 去掉 i 参数，剩下的作为模块过滤

cleanup_db()

# ===== 注册三账号（自动模式确认）=====
if INTERACTIVE:
    ans = input("\n准备注册3个测试账号（病人+管理员+医生），继续? (y/n): ").strip().lower()
    if ans != "y":
        print("已取消")
        sys.exit(0)
def fast_test(method, path, json_data=None, headers=None):
    """无交互测试——注册阶段专用"""
    url = f"{BASE}{path}"
    kwargs = {"json": json_data} if json_data else {}
    if headers: kwargs["headers"] = headers
    r = method(url, **kwargs)
    if r.status_code >= 400:
        print(f"  ⚠️ [{r.status_code}] {path} → {r.json()}")
    return r

print("\n📌 注册测试账号（自动执行，不询问）")

# 管理员由 SQL 预创建，直接登录
print("  管理员（SQL 预创建，直接登录）...")
r0 = fast_test(requests.post, "/api/v1/auth/login", {"email": ADMIN_EMAIL, "password": ADMIN_PASS})
ADMIN_TOKEN = r0.json().get("access_token", "") if r0.status_code == 200 else ""
if not ADMIN_TOKEN: print("  ❌ 管理员登录失败"); sys.exit(1)
headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
print("  ✅ 管理员登录成功")

# 管理员创建科室（医生创建前需要）并获取科室 ID
print("  初始化科室...")
r_d1 = fast_test(requests.post, "/api/v1/departments", {"name": "内科", "description": "内科疾病诊疗"}, headers=headers_admin)
dept_id = r_d1.json().get("id", 1) if r_d1.status_code == 200 else 1
fast_test(requests.post, "/api/v1/departments", {"name": "外科", "description": "外科手术"}, headers=headers_admin)

# 病人注册
print("  注册病人...")
fast_test(requests.post, "/api/v1/auth/send-code", {"email": PATIENT_EMAIL, "scene": "REGISTER"})
code = input_code()
r2 = fast_test(requests.post, "/api/v1/auth/register", {"email": PATIENT_EMAIL, "password": PASS, "name": "测试病人", "code": code, "role": 2})
if r2.status_code != 200: print(f"  ❌ 病人注册失败: {r2.json()}"); sys.exit(1)
r3 = fast_test(requests.post, "/api/v1/auth/login", {"email": PATIENT_EMAIL, "password": PASS})
PATIENT_TOKEN = r3.json().get("access_token", "") if r3.status_code == 200 else ""
headers_patient = {"Authorization": f"Bearer {PATIENT_TOKEN}"}
print("  ✅ 病人注册+登录成功")

# 医生（管理员创建，不走公开注册）
print("  管理员创建医生...")
r5 = fast_test(requests.post, "/api/v1/doctors", {"email": DOCTOR_EMAIL, "password": PASS, "name": "王医生", "department_id": dept_id, "title": "主任医师"}, headers=headers_admin)
if r5.status_code != 200: print(f"  ❌ 创建医生失败: {r5.json()}"); sys.exit(1)
doctor_id = r5.json().get("id", 1)
r6 = fast_test(requests.post, "/api/v1/auth/login", {"email": DOCTOR_EMAIL, "password": PASS})
DOCTOR_TOKEN = r6.json().get("access_token", "") if r6.status_code == 200 else ""
headers_doctor = {"Authorization": f"Bearer {DOCTOR_TOKEN}"}
print(f"  ✅ 医生创建+登录成功 (doctor_id={doctor_id})")

print("\n" + "=" * 60)
print("开始测试（token 已就绪）")
print("=" * 60)

# ============================================================
# 各模块测试 =================================================
# ============================================================

if should_run("auth"):
    print("\n📌 认证 auth")
    test("GET /me", requests.get, "/api/v1/auth/me", headers=headers_patient)
    test("PUT /me", requests.put, "/api/v1/auth/me", headers=headers_patient,
         json={"name": "测试病人改名字"})
    test("PUT /password 修改密码", requests.put, "/api/v1/auth/password", headers=headers_patient,
         json={"old_password": PASS, "new_password": "TempPass123"})
    test("PUT /password 改回密码", requests.put, "/api/v1/auth/password", headers=headers_patient,
         json={"old_password": "TempPass123", "new_password": PASS})
    # 验证码场景覆盖
    test("POST /send-code (LOGIN场景)", requests.post, "/api/v1/auth/send-code",
         json={"email": PATIENT_EMAIL, "scene": "LOGIN"})
    test("POST /send-code (RESET_PASSWORD场景)", requests.post, "/api/v1/auth/send-code",
         json={"email": PATIENT_EMAIL, "scene": "RESET_PASSWORD"})

if should_run("users"):
    print("\n📌 用户管理 users")
    test("GET /users 列表", requests.get, "/api/v1/users", headers=headers_admin)
    test("GET /users?role=2", requests.get, "/api/v1/users?role=2&page=1&page_size=5", headers=headers_admin)
    test("PUT /users/1/status", requests.put, "/api/v1/users/1/status", headers=headers_admin, json={"status": 1})
    test("POST /users/1/reset-password", requests.post, "/api/v1/users/1/reset-password", headers=headers_admin, json={"new_password": PASS})

if should_run("departments"):
    print("\n📌 科室 departments")
    test("GET /departments", requests.get, "/api/v1/departments", headers=headers_admin)
    test("POST /departments 内科", requests.post, "/api/v1/departments", headers=headers_admin,
         json={"name": "内科", "description": "内科疾病诊疗"})
    test("POST /departments 外科", requests.post, "/api/v1/departments", headers=headers_admin,
         json={"name": "外科", "description": "外科手术"})
    test("POST /departments 儿科", requests.post, "/api/v1/departments", headers=headers_admin,
         json={"name": "儿科", "description": "儿童疾病"})
    test(f"PUT /departments/{dept_id}", requests.put, f"/api/v1/departments/{dept_id}", headers=headers_admin,
         json={"description": "内科诊疗中心"})
    test(f"DELETE /departments/{dept_id+2}", requests.delete, f"/api/v1/departments/{dept_id+2}", headers=headers_admin)

if should_run("doctors"):
    print("\n📌 医生 doctors")
    test("GET /doctors", requests.get, "/api/v1/doctors", headers=headers_admin)
    test(f"GET /doctors?department_id={dept_id}", requests.get, f"/api/v1/doctors?department_id={dept_id}", headers=headers_admin)
    test(f"PUT /doctors/{doctor_id}", requests.put, f"/api/v1/doctors/{doctor_id}", headers=headers_admin,
         json={"title": "副主任医师"})
    # 创建第二个医生用于测删除
    r_doc2 = test("POST /doctors (第二个)", requests.post, "/api/v1/doctors", headers=headers_admin,
         json={"email": "doctor2@klin.edu.kg", "password": PASS, "name": "李医生", "department_id": dept_id, "title": "主治医师"})
    doc2_id = r_doc2.json().get("id", doctor_id) if r_doc2 and r_doc2.status_code == 200 else doctor_id
    test(f"DELETE /doctors/{doc2_id}", requests.delete, f"/api/v1/doctors/{doc2_id}", headers=headers_admin)

if should_run("schedules"):
    print("\n📌 排班 schedules")
    r_sch = test("POST /doctor-schedules", requests.post, "/api/v1/doctor-schedules", headers=headers_admin,
         json={"doctor_id": doctor_id, "work_date": "2026-07-15", "start_time": "08:00", "end_time": "12:00", "max_patients": 20})
    sch_id = r_sch.json().get("id", 1) if r_sch and r_sch.status_code == 200 else 1
    r_sch2 = test("POST /doctor-schedules 下午", requests.post, "/api/v1/doctor-schedules", headers=headers_admin,
         json={"doctor_id": doctor_id, "work_date": "2026-07-15", "start_time": "14:00", "end_time": "18:00", "max_patients": 15})
    sch_id2 = r_sch2.json().get("id", sch_id+1) if r_sch2 and r_sch2.status_code == 200 else sch_id+1
    test(f"GET /doctor-schedules?doctor_id={doctor_id}", requests.get, f"/api/v1/doctor-schedules?doctor_id={doctor_id}", headers=headers_admin)
    test(f"PUT /doctor-schedules/{sch_id}", requests.put, f"/api/v1/doctor-schedules/{sch_id}", headers=headers_admin, json={"max_patients": 25})
    sch2_id = sch_id + 1 if sch_id else 2
    test(f"DELETE /doctor-schedules/{sch2_id}", requests.delete, f"/api/v1/doctor-schedules/{sch2_id}", headers=headers_admin)

if should_run("patients"):
    print("\n📌 病人 patients")
    r_pl = test("GET /patients", requests.get, "/api/v1/patients", headers=headers_admin)
    patient_id = r_pl.json()[0]["id"] if r_pl and r_pl.status_code == 200 and r_pl.json() else 1
    test(f"GET /patients/{patient_id}", requests.get, f"/api/v1/patients/{patient_id}", headers=headers_patient)
    test(f"PUT /patients/{patient_id}", requests.put, f"/api/v1/patients/{patient_id}", headers=headers_patient,
         json={"gender": 1, "birth_date": "1990-01-01", "address": "北京市朝阳区", "blood_type": "A", "allergy_history": "青霉素过敏"})

if should_run("drugs"):
    print("\n📌 药品 drugs")
    r_d1 = test("POST /drugs 阿莫西林", requests.post, "/api/v1/drugs", headers=headers_admin,
         json={"name": "阿莫西林胶囊", "specification": "0.25g/粒", "unit": "盒", "price": 15.50, "stock": 100, "manufacturer": "华北制药"})
    drug_id = r_d1.json().get("id", 1) if r_d1 and r_d1.status_code == 200 else 1
    test("POST /drugs 布洛芬", requests.post, "/api/v1/drugs", headers=headers_admin,
         json={"name": "布洛芬片", "specification": "0.2g/片", "unit": "盒", "price": 20.00, "stock": 200, "manufacturer": "中美史克"})
    test("POST /drugs 维生素C", requests.post, "/api/v1/drugs", headers=headers_admin,
         json={"name": "维生素C片", "specification": "0.1g/片", "unit": "瓶", "price": 8.00, "stock": 300, "manufacturer": "东北制药"})
    test("GET /drugs", requests.get, "/api/v1/drugs", headers=headers_admin)
    test("GET /drugs?name=布洛芬", requests.get, "/api/v1/drugs?name=布洛芬", headers=headers_admin)
    test(f"PUT /drugs/{drug_id}", requests.put, f"/api/v1/drugs/{drug_id}", headers=headers_admin, json={"price": 18.00})
    test(f"PUT /drugs/{drug_id}/stock", requests.put, f"/api/v1/drugs/{drug_id}/stock", headers=headers_admin, json={"change": 50})
    test(f"DELETE /drugs/{drug_id+2}", requests.delete, f"/api/v1/drugs/{drug_id+2}", headers=headers_admin)

if should_run("appointments"):
    print("\n📌 挂号 appointments")
    r_apt = test("POST /appointments", requests.post, "/api/v1/appointments", headers=headers_patient,
         json={"doctor_id": doctor_id, "schedule_id": sch_id})
    apt_id = r_apt.json().get("id", 1) if r_apt and r_apt.status_code == 200 else 1
    test("GET /appointments", requests.get, "/api/v1/appointments", headers=headers_patient)
    test(f"PUT /appointments/{apt_id}", requests.put, f"/api/v1/appointments/{apt_id}", headers=headers_patient,
         json={"doctor_id": doctor_id})

    # 创建第二个挂号用于测试取消（同时段限号20，挂第二个没问题）
    r_apt2 = test("POST /appointments (第二个)", requests.post, "/api/v1/appointments", headers=headers_patient,
         json={"doctor_id": doctor_id, "schedule_id": sch_id})
    apt2_id = r_apt2.json().get("id") if r_apt2 and r_apt2.status_code == 200 else apt_id
    test(f"POST /appointments/{apt2_id}/cancel", requests.post, f"/api/v1/appointments/{apt2_id}/cancel", headers=headers_patient)

if should_run("diagnosis"):
    print("\n📌 诊断 diagnosis")
    test(f"POST /appointments/{apt_id}/complete", requests.post, f"/api/v1/appointments/{apt_id}/complete", headers=headers_doctor)
    r_diag = test("POST /diagnosis-records", requests.post, "/api/v1/diagnosis-records", headers=headers_doctor,
         json={"appointment_id": apt_id, "chief_complaint": "头痛三天", "diagnosis_result": "偏头痛", "prescription_advice": "注意休息"})
    diag_id = r_diag.json().get("id", 1) if r_diag and r_diag.status_code == 200 else 1
    test("GET /diagnosis-records", requests.get, "/api/v1/diagnosis-records", headers=headers_doctor)
    test(f"GET /diagnosis-records/{diag_id}", requests.get, f"/api/v1/diagnosis-records/{diag_id}", headers=headers_doctor)
    test(f"PUT /diagnosis-records/{diag_id}", requests.put, f"/api/v1/diagnosis-records/{diag_id}", headers=headers_doctor,
         json={"diagnosis_result": "血管性偏头痛", "prescription_advice": "口服布洛芬一日两次"})

if should_run("prescriptions"):
    print("\n📌 处方 prescriptions")
    r_rx = test("POST /prescriptions", requests.post, "/api/v1/prescriptions", headers=headers_doctor,
         json={"diagnosis_id": diag_id, "items": [
             {"drug_id": drug_id, "quantity": 2, "usage_method": "一日三次", "days": 7},
             {"drug_id": drug_id+1, "quantity": 1, "usage_method": "一日两次", "days": 3}]})
    rx_id = r_rx.json().get("prescription_id", 1) if r_rx and r_rx.status_code == 200 else 1
    order_id = r_rx.json().get("order_id", 1) if r_rx and r_rx.status_code == 200 else 1
    test("GET /prescriptions", requests.get, "/api/v1/prescriptions", headers=headers_doctor)
    test(f"GET /prescriptions/{rx_id}", requests.get, f"/api/v1/prescriptions/{rx_id}", headers=headers_doctor)
    test(f"PUT /prescriptions/{rx_id}", requests.put, f"/api/v1/prescriptions/{rx_id}", headers=headers_doctor,
         json={"items": [{"drug_id": drug_id, "quantity": 1, "usage_method": "一日三次", "days": 5}]})
    test("GET /drug-orders", requests.get, "/api/v1/drug-orders", headers=headers_patient)
    test(f"POST /drug-orders/{order_id}/cancel", requests.post, f"/api/v1/drug-orders/{order_id}/cancel", headers=headers_admin)

if should_run("files"):
    print("\n📌 文件 files")
    import tempfile, os
    tmpf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmpf.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    tmpf.close()
    with open(tmpf.name, "rb") as f:
        r_file = test("POST /files/upload", requests.post, "/api/v1/files/upload", headers=headers_patient,
             data={"related_type": "diagnosis_record", "related_id": diag_id}, files={"file": f})
    file_id = r_file.json().get("id", 1) if r_file and r_file.status_code == 200 else 1
    test(f"GET /files/{file_id}/download", requests.get, f"/api/v1/files/{file_id}/download", headers=headers_patient)
    test(f"DELETE /files/{file_id}", requests.delete, f"/api/v1/files/{file_id}", headers=headers_patient)
    os.unlink(tmpf.name)

if should_run("notifications"):
    print("\n📌 通知 notifications")
    test("GET /notifications", requests.get, "/api/v1/notifications", headers=headers_doctor)
    test("POST /notifications (管理员公告)", requests.post, "/api/v1/notifications", headers=headers_admin,
         json={"title": "系统维护通知", "content": "今晚22:00系统维护", "type": "SYSTEM"})
    test("GET /notifications/unread-count", requests.get, "/api/v1/notifications/unread-count", headers=headers_doctor)
    # 拿第一个通知ID标记已读
    r_nf = test("GET /notifications (取ID)", requests.get, "/api/v1/notifications", headers=headers_doctor)
    nf_id = r_nf.json()["items"][0]["id"] if r_nf and r_nf.status_code == 200 and r_nf.json().get("items") else 1
    test(f"PUT /notifications/{nf_id}/read", requests.put, f"/api/v1/notifications/{nf_id}/read", headers=headers_doctor)

if should_run("data_dict"):
    print("\n📌 数据字典 data_dict")
    test("GET /data-dict（公开）", requests.get, "/api/v1/data-dict")
    test("GET /data-dict?type=user_role", requests.get, "/api/v1/data-dict?type=user_role")
    r_dd = test("POST /data-dict", requests.post, "/api/v1/data-dict", headers=headers_admin,
         json={"dict_type": "test_type", "dict_key": 99, "dict_label": "测试值", "sort_order": 0})
    dd_id = r_dd.json().get("id", 17) if r_dd and r_dd.status_code == 200 else 17
    test(f"PUT /data-dict/{dd_id}", requests.put, f"/api/v1/data-dict/{dd_id}", headers=headers_admin,
         json={"dict_label": "更新测试值"})
    test(f"DELETE /data-dict/{dd_id}", requests.delete, f"/api/v1/data-dict/{dd_id}", headers=headers_admin)

if should_run("sys_config"):
    print("\n📌 系统配置 sys_config")
    test("GET /system-config（公开）", requests.get, "/api/v1/system-config")
    r_sc = test("POST /system-config", requests.post, "/api/v1/system-config", headers=headers_admin,
         json={"config_key": "test_config", "config_value": "hello", "description": "测试配置"})
    sc_id = r_sc.json().get("id", 1) if r_sc and r_sc.status_code == 200 else 1
    test(f"PUT /system-config/{sc_id}", requests.put, f"/api/v1/system-config/{sc_id}", headers=headers_admin,
         json={"config_value": "updated"})
    test(f"DELETE /system-config/{sc_id}", requests.delete, f"/api/v1/system-config/{sc_id}", headers=headers_admin)

if should_run("audit_logs"):
    print("\n📌 操作日志 audit_logs")
    test("GET /audit-logs", requests.get, "/api/v1/audit-logs", headers=headers_admin)

# 最后做会破坏数据的操作
print("\n📌 收尾：软删除测试")
test(f"DELETE /patients/{patient_id}", requests.delete, f"/api/v1/patients/{patient_id}", headers=headers_admin)

print("\n📌 登出")
test("POST /auth/logout", requests.post, "/api/v1/auth/logout", headers=headers_patient)

print_total()
