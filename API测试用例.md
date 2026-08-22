# MedFlow API 测试用例文档

> 基于 `MedFlow-backend/test_api.py` 整理，按测试脚本执行顺序排列。每个接口一个独立 curl，复制即用。
>
> **变量说明**：命令中的 `{ADMIN_TOKEN}`、`{PATIENT_TOKEN}`、`{DOCTOR_TOKEN}` 以及各 `{xxx_id}` 需替换为实际值。
>
> - **基础地址**: `http://localhost:8001`
> - **测试账号**:
>   - 病人: `knc8t@yangs.edu.kg` / 密码 `Test123456`
>   - 管理员: `19070924661@163.com` / 密码 `Admin123456`
>   - 医生: `3575771702@qq.com` / 密码 `Test123456`

---

## 前置准备

### 1. 数据库清理

清空以下表，SQL 预创建管理员（id=1, role=0, status=1, password=Admin123456 的哈希）：

prescription_item, drug_order, prescription, diagnosis_record, appointment, file_attachment, notification, doctor_schedule, patient, doctor, user, verification_code。

清理 `data_dict` 中 `dict_type='test_type'`、`system_config` 中 `config_key='test_config'` 的残留数据。

### 2. 管理员登录 → 获取 `{ADMIN_TOKEN}`

```bash
curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"19070924661@163.com","password":"Admin123456"}'
```

### 3. 初始化科室 → 获取 `{dept_id}`

```bash
curl -s -X POST http://localhost:8001/api/v1/departments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"name":"内科","description":"内科疾病诊疗"}'
```

```bash
curl -s -X POST http://localhost:8001/api/v1/departments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"name":"外科","description":"外科手术"}'
```

### 4. 病人注册 → 获取 `{PATIENT_TOKEN}`

```bash
curl -s -X POST http://localhost:8001/api/v1/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"email":"knc8t@yangs.edu.kg","scene":"REGISTER"}'
```

```bash
curl -s -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"knc8t@yangs.edu.kg","password":"Test123456","name":"测试病人","code":"<验证码>","role":2}'
```

```bash
curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"knc8t@yangs.edu.kg","password":"Test123456"}'
```

### 5. 管理员创建医生 + 医生登录 → 获取 `{doctor_id}` 和 `{DOCTOR_TOKEN}`

```bash
curl -s -X POST http://localhost:8001/api/v1/doctors \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"email":"3575771702@qq.com","password":"Test123456","name":"王医生","department_id":{dept_id},"title":"主任医师"}'
```

```bash
curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"3575771702@qq.com","password":"Test123456"}'
```

---

## 模块测试

### 一、认证 auth

#### 1-1 获取当前用户 `GET /api/v1/auth/me`

预期 `200` | 认证 `PATIENT_TOKEN`

```bash
curl -s http://localhost:8001/api/v1/auth/me \
  -H "Authorization: Bearer {PATIENT_TOKEN}"
```

#### 1-2 更新个人信息 `PUT /api/v1/auth/me`

预期 `200` | 认证 `PATIENT_TOKEN`

```bash
curl -s -X PUT http://localhost:8001/api/v1/auth/me \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {PATIENT_TOKEN}" \
  -d '{"name":"测试病人改名字"}'
```

#### 1-3 修改密码 `PUT /api/v1/auth/password`

预期 `200` | 认证 `PATIENT_TOKEN`

```bash
curl -s -X PUT http://localhost:8001/api/v1/auth/password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {PATIENT_TOKEN}" \
  -d '{"old_password":"Test123456","new_password":"TempPass123"}'
```

#### 1-4 改回原密码 `PUT /api/v1/auth/password`

预期 `200` | 认证 `PATIENT_TOKEN`

```bash
curl -s -X PUT http://localhost:8001/api/v1/auth/password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {PATIENT_TOKEN}" \
  -d '{"old_password":"TempPass123","new_password":"Test123456"}'
```

#### 1-5 发送验证码(登录场景) `POST /api/v1/auth/send-code`

预期 `200` | 无需认证

```bash
curl -s -X POST http://localhost:8001/api/v1/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"email":"knc8t@yangs.edu.kg","scene":"LOGIN"}'
```

#### 1-6 发送验证码(重置密码场景) `POST /api/v1/auth/send-code`

预期 `200` | 无需认证

```bash
curl -s -X POST http://localhost:8001/api/v1/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"email":"knc8t@yangs.edu.kg","scene":"RESET_PASSWORD"}'
```

---

### 二、用户管理 users

> 均需 `{ADMIN_TOKEN}`

#### 2-1 用户列表 `GET /api/v1/users`

预期 `200`

```bash
curl -s http://localhost:8001/api/v1/users \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

#### 2-2 按角色筛选 `GET /api/v1/users?role=2&page=1&page_size=5`

预期 `200`

```bash
curl -s "http://localhost:8001/api/v1/users?role=2&page=1&page_size=5" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

#### 2-3 修改用户状态 `PUT /api/v1/users/1/status`

预期 `200`

```bash
curl -s -X PUT http://localhost:8001/api/v1/users/1/status \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"status":1}'
```

#### 2-4 重置用户密码 `POST /api/v1/users/1/reset-password`

预期 `200`

```bash
curl -s -X POST http://localhost:8001/api/v1/users/1/reset-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"new_password":"Test123456"}'
```

---

### 三、科室 departments

> 均需 `{ADMIN_TOKEN}`

#### 3-1 科室列表 `GET /api/v1/departments`

预期 `200`

```bash
curl -s http://localhost:8001/api/v1/departments \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

#### 3-2 创建内科 `POST /api/v1/departments`

预期 `200`

```bash
curl -s -X POST http://localhost:8001/api/v1/departments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"name":"内科","description":"内科疾病诊疗"}'
```

#### 3-3 创建外科 `POST /api/v1/departments`

预期 `200`

```bash
curl -s -X POST http://localhost:8001/api/v1/departments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"name":"外科","description":"外科手术"}'
```

#### 3-4 创建儿科 `POST /api/v1/departments`

预期 `200`

```bash
curl -s -X POST http://localhost:8001/api/v1/departments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"name":"儿科","description":"儿童疾病"}'
```

#### 3-5 更新科室 `PUT /api/v1/departments/{dept_id}`

预期 `200`

```bash
curl -s -X PUT http://localhost:8001/api/v1/departments/{dept_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"description":"内科诊疗中心"}'
```

#### 3-6 删除科室 `DELETE /api/v1/departments/{dept_id+2}`

预期 `200`

```bash
curl -s -X DELETE http://localhost:8001/api/v1/departments/{dept_id+2} \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

### 四、医生 doctors

> 均需 `{ADMIN_TOKEN}`

#### 4-1 医生列表 `GET /api/v1/doctors`

预期 `200`

```bash
curl -s http://localhost:8001/api/v1/doctors \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

#### 4-2 按科室筛选医生 `GET /api/v1/doctors?department_id={dept_id}`

预期 `200`

```bash
curl -s "http://localhost:8001/api/v1/doctors?department_id={dept_id}" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

#### 4-3 更新医生信息 `PUT /api/v1/doctors/{doctor_id}`

预期 `200`

```bash
curl -s -X PUT http://localhost:8001/api/v1/doctors/{doctor_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"title":"副主任医师"}'
```

#### 4-4 创建第二个医生 `POST /api/v1/doctors`

预期 `200` → 获取 `{doc2_id}` 供删除用

```bash
curl -s -X POST http://localhost:8001/api/v1/doctors \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"email":"doctor2@klin.edu.kg","password":"Test123456","name":"李医生","department_id":{dept_id},"title":"主治医师"}'
```

#### 4-5 删除医生 `DELETE /api/v1/doctors/{doc2_id}`

预期 `200`

```bash
curl -s -X DELETE http://localhost:8001/api/v1/doctors/{doc2_id} \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

### 五、排班 schedules

> 均需 `{ADMIN_TOKEN}`。`{sch_id}` 为上午排班 ID。

#### 5-1 创建上午排班 `POST /api/v1/doctor-schedules`

预期 `200` → 获取 `{sch_id}`

```bash
curl -s -X POST http://localhost:8001/api/v1/doctor-schedules \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"doctor_id":{doctor_id},"work_date":"2026-07-15","start_time":"08:00","end_time":"12:00","max_patients":20}'
```

#### 5-2 创建下午排班 `POST /api/v1/doctor-schedules`

预期 `200`

```bash
curl -s -X POST http://localhost:8001/api/v1/doctor-schedules \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"doctor_id":{doctor_id},"work_date":"2026-07-15","start_time":"14:00","end_time":"18:00","max_patients":15}'
```

#### 5-3 查询医生排班 `GET /api/v1/doctor-schedules?doctor_id={doctor_id}`

预期 `200`

```bash
curl -s "http://localhost:8001/api/v1/doctor-schedules?doctor_id={doctor_id}" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

#### 5-4 更新排班 `PUT /api/v1/doctor-schedules/{sch_id}`

预期 `200`

```bash
curl -s -X PUT http://localhost:8001/api/v1/doctor-schedules/{sch_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"max_patients":25}'
```

#### 5-5 删除排班 `DELETE /api/v1/doctor-schedules/{sch_id+1}`

预期 `200`

```bash
curl -s -X DELETE http://localhost:8001/api/v1/doctor-schedules/{sch_id+1} \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

### 六、病人 patients

#### 6-1 病人列表 `GET /api/v1/patients`

预期 `200` | 认证 `ADMIN_TOKEN` → 获取 `{patient_id}`

```bash
curl -s http://localhost:8001/api/v1/patients \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

#### 6-2 病人详情 `GET /api/v1/patients/{patient_id}`

预期 `200` | 认证 `PATIENT_TOKEN`

```bash
curl -s http://localhost:8001/api/v1/patients/{patient_id} \
  -H "Authorization: Bearer {PATIENT_TOKEN}"
```

#### 6-3 更新病人信息 `PUT /api/v1/patients/{patient_id}`

预期 `200` | 认证 `PATIENT_TOKEN`

```bash
curl -s -X PUT http://localhost:8001/api/v1/patients/{patient_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {PATIENT_TOKEN}" \
  -d '{"gender":1,"birth_date":"1990-01-01","address":"北京市朝阳区","blood_type":"A","allergy_history":"青霉素过敏"}'
```

---

### 七、药品 drugs

> 均需 `{ADMIN_TOKEN}`。`{drug_id}` 为阿莫西林 ID。

#### 7-1 创建阿莫西林 `POST /api/v1/drugs`

预期 `200` → 获取 `{drug_id}`

```bash
curl -s -X POST http://localhost:8001/api/v1/drugs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"name":"阿莫西林胶囊","specification":"0.25g/粒","unit":"盒","price":15.50,"stock":100,"manufacturer":"华北制药"}'
```

#### 7-2 创建布洛芬 `POST /api/v1/drugs`

预期 `200`

```bash
curl -s -X POST http://localhost:8001/api/v1/drugs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"name":"布洛芬片","specification":"0.2g/片","unit":"盒","price":20.00,"stock":200,"manufacturer":"中美史克"}'
```

#### 7-3 创建维生素C `POST /api/v1/drugs`

预期 `200`

```bash
curl -s -X POST http://localhost:8001/api/v1/drugs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"name":"维生素C片","specification":"0.1g/片","unit":"瓶","price":8.00,"stock":300,"manufacturer":"东北制药"}'
```

#### 7-4 药品列表 `GET /api/v1/drugs`

预期 `200`

```bash
curl -s http://localhost:8001/api/v1/drugs \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

#### 7-5 按名称搜索药品 `GET /api/v1/drugs?name=布洛芬`

预期 `200`

```bash
curl -s "http://localhost:8001/api/v1/drugs?name=%E5%B8%83%E6%B4%9B%E8%8A%AC" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

#### 7-6 更新药品价格 `PUT /api/v1/drugs/{drug_id}`

预期 `200`

```bash
curl -s -X PUT http://localhost:8001/api/v1/drugs/{drug_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"price":18.00}'
```

#### 7-7 更新药品库存 `PUT /api/v1/drugs/{drug_id}/stock`

预期 `200`

```bash
curl -s -X PUT http://localhost:8001/api/v1/drugs/{drug_id}/stock \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"change":50}'
```

#### 7-8 删除药品 `DELETE /api/v1/drugs/{drug_id+2}`

预期 `200`

```bash
curl -s -X DELETE http://localhost:8001/api/v1/drugs/{drug_id+2} \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

### 八、挂号 appointments

#### 8-1 创建挂号 `POST /api/v1/appointments`

预期 `200` | 认证 `PATIENT_TOKEN` → 获取 `{apt_id}`

```bash
curl -s -X POST http://localhost:8001/api/v1/appointments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {PATIENT_TOKEN}" \
  -d '{"doctor_id":{doctor_id},"schedule_id":{sch_id}}'
```

#### 8-2 挂号列表 `GET /api/v1/appointments`

预期 `200` | 认证 `PATIENT_TOKEN`

```bash
curl -s http://localhost:8001/api/v1/appointments \
  -H "Authorization: Bearer {PATIENT_TOKEN}"
```

#### 8-3 更新挂号 `PUT /api/v1/appointments/{apt_id}`

预期 `200` | 认证 `PATIENT_TOKEN`

```bash
curl -s -X PUT http://localhost:8001/api/v1/appointments/{apt_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {PATIENT_TOKEN}" \
  -d '{"doctor_id":{doctor_id}}'
```

#### 8-4 创建第二个挂号 `POST /api/v1/appointments`

预期 `200` | 认证 `PATIENT_TOKEN` → 获取 `{apt2_id}`

```bash
curl -s -X POST http://localhost:8001/api/v1/appointments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {PATIENT_TOKEN}" \
  -d '{"doctor_id":{doctor_id},"schedule_id":{sch_id}}'
```

#### 8-5 取消挂号 `POST /api/v1/appointments/{apt2_id}/cancel`

预期 `200` | 认证 `PATIENT_TOKEN`

```bash
curl -s -X POST http://localhost:8001/api/v1/appointments/{apt2_id}/cancel \
  -H "Authorization: Bearer {PATIENT_TOKEN}"
```

---

### 九、诊断 diagnosis

#### 9-1 完成挂号 `POST /api/v1/appointments/{apt_id}/complete`

预期 `200` | 认证 `DOCTOR_TOKEN`

```bash
curl -s -X POST http://localhost:8001/api/v1/appointments/{apt_id}/complete \
  -H "Authorization: Bearer {DOCTOR_TOKEN}"
```

#### 9-2 创建诊断记录 `POST /api/v1/diagnosis-records`

预期 `200` | 认证 `DOCTOR_TOKEN` → 获取 `{diag_id}`

```bash
curl -s -X POST http://localhost:8001/api/v1/diagnosis-records \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {DOCTOR_TOKEN}" \
  -d '{"appointment_id":{apt_id},"chief_complaint":"头痛三天","diagnosis_result":"偏头痛","prescription_advice":"注意休息"}'
```

#### 9-3 诊断列表 `GET /api/v1/diagnosis-records`

预期 `200` | 认证 `DOCTOR_TOKEN`

```bash
curl -s http://localhost:8001/api/v1/diagnosis-records \
  -H "Authorization: Bearer {DOCTOR_TOKEN}"
```

#### 9-4 诊断详情 `GET /api/v1/diagnosis-records/{diag_id}`

预期 `200` | 认证 `DOCTOR_TOKEN`

```bash
curl -s http://localhost:8001/api/v1/diagnosis-records/{diag_id} \
  -H "Authorization: Bearer {DOCTOR_TOKEN}"
```

#### 9-5 更新诊断 `PUT /api/v1/diagnosis-records/{diag_id}`

预期 `200` | 认证 `DOCTOR_TOKEN`

```bash
curl -s -X PUT http://localhost:8001/api/v1/diagnosis-records/{diag_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {DOCTOR_TOKEN}" \
  -d '{"diagnosis_result":"血管性偏头痛","prescription_advice":"口服布洛芬一日两次"}'
```

---

### 十、处方 + 订单 prescriptions

#### 10-1 创建处方 `POST /api/v1/prescriptions`

预期 `200` | 认证 `DOCTOR_TOKEN` → 获取 `{rx_id}` 和 `{order_id}`

```bash
curl -s -X POST http://localhost:8001/api/v1/prescriptions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {DOCTOR_TOKEN}" \
  -d '{"diagnosis_id":{diag_id},"items":[{"drug_id":{drug_id},"quantity":2,"usage_method":"一日三次","days":7},{"drug_id":{drug_id+1},"quantity":1,"usage_method":"一日两次","days":3}]}'
```

#### 10-2 处方列表 `GET /api/v1/prescriptions`

预期 `200` | 认证 `DOCTOR_TOKEN`

```bash
curl -s http://localhost:8001/api/v1/prescriptions \
  -H "Authorization: Bearer {DOCTOR_TOKEN}"
```

#### 10-3 处方详情 `GET /api/v1/prescriptions/{rx_id}`

预期 `200` | 认证 `DOCTOR_TOKEN`

```bash
curl -s http://localhost:8001/api/v1/prescriptions/{rx_id} \
  -H "Authorization: Bearer {DOCTOR_TOKEN}"
```

#### 10-4 更新处方 `PUT /api/v1/prescriptions/{rx_id}`

预期 `200` | 认证 `DOCTOR_TOKEN`

```bash
curl -s -X PUT http://localhost:8001/api/v1/prescriptions/{rx_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {DOCTOR_TOKEN}" \
  -d '{"items":[{"drug_id":{drug_id},"quantity":1,"usage_method":"一日三次","days":5}]}'
```

#### 10-5 药品订单列表 `GET /api/v1/drug-orders`

预期 `200` | 认证 `PATIENT_TOKEN` → 获取 `{order_id}`

```bash
curl -s http://localhost:8001/api/v1/drug-orders \
  -H "Authorization: Bearer {PATIENT_TOKEN}"
```

#### 10-6 取消订单 `POST /api/v1/drug-orders/{order_id}/cancel`

预期 `200` | 认证 `ADMIN_TOKEN`

```bash
curl -s -X POST http://localhost:8001/api/v1/drug-orders/{order_id}/cancel \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

### 十一、文件 files

> 先准备测试文件：`printf '\x89PNG\r\n\x1a\n' > /tmp/test.png && head -c 100 /dev/zero >> /tmp/test.png`

#### 11-1 上传文件 `POST /api/v1/files/upload`

预期 `200` | 认证 `PATIENT_TOKEN` → 获取 `{file_id}`

```bash
curl -s -X POST http://localhost:8001/api/v1/files/upload \
  -H "Authorization: Bearer {PATIENT_TOKEN}" \
  -F "related_type=diagnosis_record" \
  -F "related_id={diag_id}" \
  -F "file=@/tmp/test.png"
```

#### 11-2 下载文件 `GET /api/v1/files/{file_id}/download`

预期 `200` | 认证 `PATIENT_TOKEN`

```bash
curl -s http://localhost:8001/api/v1/files/{file_id}/download \
  -H "Authorization: Bearer {PATIENT_TOKEN}"
```

#### 11-3 删除文件 `DELETE /api/v1/files/{file_id}`

预期 `200` | 认证 `PATIENT_TOKEN`

```bash
curl -s -X DELETE http://localhost:8001/api/v1/files/{file_id} \
  -H "Authorization: Bearer {PATIENT_TOKEN}"
```

---

### 十二、通知 notifications

> 均需 `{DOCTOR_TOKEN}`。`{nf_id}` 为通知列表中第一条的 ID。

#### 12-1 通知列表 `GET /api/v1/notifications`

预期 `200`

```bash
curl -s http://localhost:8001/api/v1/notifications \
  -H "Authorization: Bearer {DOCTOR_TOKEN}"
```

#### 12-2 未读数量 `GET /api/v1/notifications/unread-count`

预期 `200`

```bash
curl -s http://localhost:8001/api/v1/notifications/unread-count \
  -H "Authorization: Bearer {DOCTOR_TOKEN}"
```

#### 12-3 通知列表(取ID) `GET /api/v1/notifications`

预期 `200` → 从中获取 `{nf_id}`

```bash
curl -s http://localhost:8001/api/v1/notifications \
  -H "Authorization: Bearer {DOCTOR_TOKEN}"
```

#### 12-4 标记已读 `PUT /api/v1/notifications/{nf_id}/read`

预期 `200`

```bash
curl -s -X PUT http://localhost:8001/api/v1/notifications/{nf_id}/read \
  -H "Authorization: Bearer {DOCTOR_TOKEN}"
```

---

### 十三、数据字典 data_dict

#### 13-1 字典列表(公开) `GET /api/v1/data-dict`

预期 `200` | 无需认证

```bash
curl -s http://localhost:8001/api/v1/data-dict
```

#### 13-2 按类型筛选 `GET /api/v1/data-dict?type=user_role`

预期 `200` | 无需认证

```bash
curl -s "http://localhost:8001/api/v1/data-dict?type=user_role"
```

#### 13-3 创建字典项 `POST /api/v1/data-dict`

预期 `200` | 认证 `ADMIN_TOKEN` → 获取 `{dd_id}`

```bash
curl -s -X POST http://localhost:8001/api/v1/data-dict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"dict_type":"test_type","dict_key":99,"dict_label":"测试值","sort_order":0}'
```

#### 13-4 更新字典项 `PUT /api/v1/data-dict/{dd_id}`

预期 `200` | 认证 `ADMIN_TOKEN`

```bash
curl -s -X PUT http://localhost:8001/api/v1/data-dict/{dd_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"dict_label":"更新测试值"}'
```

#### 13-5 删除字典项 `DELETE /api/v1/data-dict/{dd_id}`

预期 `200` | 认证 `ADMIN_TOKEN`

```bash
curl -s -X DELETE http://localhost:8001/api/v1/data-dict/{dd_id} \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

### 十四、系统配置 sys_config

#### 14-1 配置列表(公开) `GET /api/v1/system-config`

预期 `200` | 无需认证

```bash
curl -s http://localhost:8001/api/v1/system-config
```

#### 14-2 创建配置 `POST /api/v1/system-config`

预期 `200` | 认证 `ADMIN_TOKEN` → 获取 `{sc_id}`

```bash
curl -s -X POST http://localhost:8001/api/v1/system-config \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"config_key":"test_config","config_value":"hello","description":"测试配置"}'
```

#### 14-3 更新配置 `PUT /api/v1/system-config/{sc_id}`

预期 `200` | 认证 `ADMIN_TOKEN`

```bash
curl -s -X PUT http://localhost:8001/api/v1/system-config/{sc_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"config_value":"updated"}'
```

#### 14-4 删除配置 `DELETE /api/v1/system-config/{sc_id}`

预期 `200` | 认证 `ADMIN_TOKEN`

```bash
curl -s -X DELETE http://localhost:8001/api/v1/system-config/{sc_id} \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

### 十五、操作日志 audit_logs

#### 15-1 日志列表 `GET /api/v1/audit-logs`

预期 `200` | 认证 `ADMIN_TOKEN`

```bash
curl -s http://localhost:8001/api/v1/audit-logs \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

## 收尾清理

#### 16-1 软删除病人 `DELETE /api/v1/patients/{patient_id}`

预期 `200` | 认证 `ADMIN_TOKEN`

```bash
curl -s -X DELETE http://localhost:8001/api/v1/patients/{patient_id} \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

#### 16-2 登出 `POST /api/v1/auth/logout`

预期 `200` | 认证 `PATIENT_TOKEN`

```bash
curl -s -X POST http://localhost:8001/api/v1/auth/logout \
  -H "Authorization: Bearer {PATIENT_TOKEN}"
```

---

## 统计

| 模块 | 接口数 |
|------|--------|
| auth（认证） | 6 |
| users（用户管理） | 4 |
| departments（科室） | 6 |
| doctors（医生） | 5 |
| schedules（排班） | 5 |
| patients（病人） | 3 |
| drugs（药品） | 8 |
| appointments（挂号） | 5 |
| diagnosis（诊断） | 5 |
| prescriptions（处方+订单） | 6 |
| files（文件） | 3 |
| notifications（通知） | 4 |
| data_dict（数据字典） | 5 |
| sys_config（系统配置） | 4 |
| audit_logs（操作日志） | 1 |
| 收尾（删除+登出） | 2 |
| **合计** | **72** |
