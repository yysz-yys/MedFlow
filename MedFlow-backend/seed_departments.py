"""
硬删除所有科室并重新插入医院实际科室数据，ID从1开始连续编号。
运行方式: cd MedFlow-backend && python seed_departments.py
"""
from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url_sync, echo=False)

# 基于三级医院实际情况的科室列表 (name, description)
DEPARTMENTS = [
    # === 内科系统 ===
    ("心血管内科", "冠心病、高血压、心律失常、心力衰竭等心血管疾病的诊治"),
    ("呼吸内科", "肺炎、哮喘、慢阻肺、肺癌等呼吸系统疾病的诊治"),
    ("消化内科", "胃炎、胃溃疡、肝炎、胰腺炎、肠炎等消化系统疾病的诊治"),
    ("神经内科", "脑梗死、脑出血、帕金森病、癫痫、头痛眩晕等神经系统疾病的诊治"),
    ("肾内科", "肾炎、肾病综合征、肾功能衰竭等肾脏疾病的诊治及血液透析"),
    ("内分泌科", "糖尿病、甲亢、甲减、痛风、骨质疏松等内分泌代谢疾病的诊治"),
    ("血液科", "贫血、白血病、淋巴瘤、骨髓瘤等血液系统疾病的诊治"),
    ("风湿免疫科", "类风湿关节炎、系统性红斑狼疮、强直性脊柱炎等风湿免疫疾病的诊治"),
    ("肿瘤内科", "肺癌、胃癌、肝癌、乳腺癌等实体瘤的化疗、靶向治疗及免疫治疗"),
    ("老年病科", "老年多系统疾病的综合诊治、老年综合征评估与管理"),

    # === 外科系统 ===
    ("普外科", "甲状腺、乳腺、胃肠、肝胆胰等疾病的常规及微创手术治疗"),
    ("骨科", "骨折、关节置换、脊柱疾病、运动损伤等骨骼肌肉系统疾病的手术及康复"),
    ("泌尿外科", "肾结石、前列腺疾病、膀胱肿瘤等泌尿系统疾病的手术及微创治疗"),
    ("神经外科", "颅脑外伤、脑肿瘤、脑血管疾病、脊髓疾病的手术治疗"),
    ("胸外科", "肺癌、食管癌、纵隔肿瘤等胸部疾病的手术治疗"),
    ("心血管外科", "冠心病搭桥、心脏瓣膜置换、先天性心脏病等心血管手术"),
    ("烧伤整形外科", "烧伤救治、瘢痕修复、体表肿瘤切除及整形美容手术"),

    # === 妇产儿科 ===
    ("妇产科", "妇科炎症、肿瘤、内分泌疾病的诊治，产前检查、分娩及产后康复"),
    ("儿科", "儿童常见病、多发病的诊治，新生儿疾病筛查及儿童保健"),
    ("新生儿科", "早产儿、低体重儿及新生儿疾病的监护与治疗"),

    # === 五官科 ===
    ("眼科", "白内障、青光眼、眼底病、屈光不正等眼部疾病的诊治及手术"),
    ("耳鼻喉科", "中耳炎、鼻炎、咽喉炎、打鼾、听力障碍等疾病的诊治及手术"),
    ("口腔科", "牙体牙髓、牙周病、口腔修复、口腔正畸及口腔颌面外科"),

    # === 其他临床科室 ===
    ("皮肤科", "湿疹、银屑病、荨麻疹、痤疮等皮肤病及性传播疾病的诊治"),
    ("感染科", "肝炎、结核、艾滋病、发热待查等感染性疾病的诊治"),
    ("中医科", "中药调理、针灸推拿、拔罐等中医传统诊疗方法"),
    ("康复医学科", "脑卒中后遗症、骨折术后、运动损伤等疾病的康复评定与治疗"),
    ("急诊科", "各类急危重症的抢救与初步处置，24小时接诊"),
    ("麻醉科", "临床麻醉、疼痛治疗、无痛诊疗及危重症抢救"),
    ("重症医学科(ICU)", "多器官功能衰竭、重症感染、严重创伤等危重症的监护与治疗"),
    ("精神科(心理卫生)", "抑郁症、焦虑症、失眠症、精神分裂症等精神心理疾病的诊治"),
    ("疼痛科", "颈肩腰腿痛、带状疱疹后神经痛、癌性疼痛等慢性疼痛的综合治疗"),
    ("全科医学科", "常见病、多发病的综合性诊疗，慢性病管理与健康管理"),
    ("介入科", "肿瘤介入、血管介入、非血管介入等微创介入诊疗"),

    # === 医技科室 ===
    ("检验科", "血常规、生化、免疫、微生物、分子生物学等检验项目"),
    ("放射科", "X线、CT、MRI等影像学检查与诊断"),
    ("超声科", "腹部、心脏、血管、妇产科、小器官等超声检查与诊断"),
    ("核医学科", "ECT、PET-CT等核医学影像检查与放射性核素治疗"),
    ("病理科", "组织和细胞学病理诊断、术中冰冻、免疫组化及分子病理"),
    ("内镜中心", "胃镜、肠镜、支气管镜、膀胱镜等内镜检查与治疗"),
    ("药剂科", "药品采购、调剂、临床药学、合理用药监测与咨询"),
    ("输血科", "血型鉴定、交叉配血、血液成分制备与输血管理"),
    ("营养科", "临床营养评估、治疗膳食配制、肠内肠外营养支持"),
    ("心电诊断科", "心电图、动态心电图、动态血压等心电生理检查与诊断"),

    # === 其他 ===
    ("体检中心", "个人及团体健康体检、入职体检、驾驶员体检及健康管理"),
    ("预防保健科", "预防接种、传染病防控、健康教育及慢病筛查"),
    ("消毒供应中心", "医疗器械清洗消毒、灭菌及无菌物品供应"),
]

with engine.connect() as conn:
    # 0. 获取旧科室名称→旧ID映射（用于后续FK迁移）
    old_result = conn.execute(text("SELECT id, name FROM department ORDER BY id"))
    old_name_to_id = {row[1]: row[0] for row in old_result.fetchall()}
    print(f"当前科室: {len(old_name_to_id)} 个, IDs: {sorted(old_name_to_id.values())}")

    # 1. 构建旧ID→新ID映射（按新列表顺序重新分配）
    old_to_new = {}
    for new_id, (name, _desc) in enumerate(DEPARTMENTS, start=1):
        if name in old_name_to_id:
            old_to_new[old_name_to_id[name]] = new_id

    print(f"ID映射: {old_to_new}")

    # 2. 关闭FK检查，更新引用表的外键
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    for tbl in ["doctor", "appointment"]:
        for old_id, new_id in old_to_new.items():
            result = conn.execute(
                text(f"UPDATE {tbl} SET department_id = :new WHERE department_id = :old"),
                {"old": old_id, "new": new_id},
            )
            if result.rowcount:
                print(f"  {tbl}.department_id: {old_id} -> {new_id} ({result.rowcount} rows)")

    # 3. 清空department表，重置自增
    conn.execute(text("DELETE FROM department"))
    conn.execute(text("ALTER TABLE department AUTO_INCREMENT = 1"))
    conn.commit()
    print("已清空 department 表，自增重置为 1")

    # 4. 插入新科室（ID从1开始连续）
    for i, (name, desc) in enumerate(DEPARTMENTS, start=1):
        conn.execute(
            text(
                "INSERT INTO department (id, name, description, created_at, updated_at) "
                "VALUES (:id, :name, :desc, NOW(), NOW())"
            ),
            {"id": i, "name": name, "desc": desc},
        )
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    conn.commit()
    print(f"已插入 {len(DEPARTMENTS)} 个科室（ID 1~{len(DEPARTMENTS)}）")

# 5. 验证
with engine.connect() as conn:
    result = conn.execute(text("SELECT id, name, description FROM department ORDER BY id"))
    rows = result.fetchall()
    print(f"\n科室列表 ({len(rows)} 个):")
    for row in rows:
        print(f"  {row[0]:2d}. {row[1]} — {row[2][:40]}...")

    # 验证FK引用完整性
    dr = conn.execute(text("SELECT DISTINCT department_id FROM doctor ORDER BY department_id")).fetchall()
    ar = conn.execute(text("SELECT DISTINCT department_id FROM appointment ORDER BY department_id")).fetchall()
    print(f"\nFK验证: doctor引用 {[r[0] for r in dr]}, appointment引用 {[r[0] for r in ar]}")

print("\nDone.")
