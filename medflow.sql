-- ============================================================
-- 网上医疗记录系统（云诊易 MedFlow）— 数据库建表脚本 v2.1
-- 变更说明：
--   2.0: user.role/user.status/appointment.status 改为 TINYINT 枚举；
--        新增 prescription 处方头表，处方明细与订单挂在处方上
--   2.1: department/doctor/patient/drug 新增 deleted_at 软删除字段
-- ============================================================

CREATE DATABASE IF NOT EXISTS medflow
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE medflow;

-- ============================================================
-- 1. 用户表
--   软删除策略：不使用 deleted_at，通过 status=0（禁用）实现
-- ============================================================
CREATE TABLE `user` (
    `id`         BIGINT       NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `password`   VARCHAR(255) NOT NULL                 COMMENT '密码（加密存储）',
    `name`       VARCHAR(50)  NOT NULL                 COMMENT '姓名',
    `email`      VARCHAR(100) NOT NULL                 COMMENT '邮箱（登录凭证）',
    `phone`      VARCHAR(20)                           COMMENT '手机号（选填）',
    `role`       TINYINT      NOT NULL                 COMMENT '角色：0=管理员 / 1=医生 / 2=病人',
    `status`     TINYINT      NOT NULL DEFAULT 1       COMMENT '状态：0=禁用 / 1=正常',
    `last_login` DATETIME                              COMMENT '最后登录时间',
    `created_at` DATETIME     NOT NULL                 COMMENT '创建时间',
    `updated_at` DATETIME     NOT NULL                 COMMENT '修改时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_email` (`email`),
    UNIQUE KEY `uk_phone` (`phone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================================
-- 2. 科室表
--   软删除策略：deleted_at（科室撤销后历史挂号/诊断/处方的引用不能断链）
-- ============================================================
CREATE TABLE `department` (
    `id`          BIGINT       NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `name`        VARCHAR(50)  NOT NULL                 COMMENT '名称',
    `description` VARCHAR(255)                          COMMENT '描述',
    `deleted_at`  DATETIME                              COMMENT '软删除时间（NULL=正常）',
    `created_at`  DATETIME     NOT NULL                 COMMENT '创建时间',
    `updated_at`  DATETIME     NOT NULL                 COMMENT '修改时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='科室表';

-- ============================================================
-- 3. 医生表
--   软删除策略：deleted_at（医生离职后其历史诊断/处方记录必须可追溯）
-- ============================================================
CREATE TABLE `doctor` (
    `id`            BIGINT       NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `user_id`       BIGINT       NOT NULL                 COMMENT '用户ID（一对一）',
    `department_id` BIGINT       NOT NULL                 COMMENT '科室ID（多对一）',
    `title`         VARCHAR(50)                           COMMENT '职称，如主任医师',
    `introduction`  VARCHAR(500)                          COMMENT '简介',
    `deleted_at`    DATETIME                              COMMENT '软删除时间（NULL=正常）',
    `created_at`    DATETIME     NOT NULL                 COMMENT '创建时间',
    `updated_at`    DATETIME     NOT NULL                 COMMENT '修改时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_id` (`user_id`),
    KEY `idx_department_id` (`department_id`),
    CONSTRAINT `fk_doctor_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
    CONSTRAINT `fk_doctor_department` FOREIGN KEY (`department_id`) REFERENCES `department` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='医生表';

-- ============================================================
-- 4. 医生排班表
--   每位医生独立设置出诊时段，挂号时根据排班动态生成可选时间
--   一个医生可以有多个排班时段
-- ============================================================
CREATE TABLE `doctor_schedule` (
    `id`           BIGINT    NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `doctor_id`    BIGINT    NOT NULL                 COMMENT '医生ID',
    `work_date`    DATE      NOT NULL                 COMMENT '出诊日期',
    `start_time`   TIME      NOT NULL                 COMMENT '开始时间，如 08:00',
    `end_time`     TIME      NOT NULL                 COMMENT '结束时间，如 12:00',
    `max_patients` INT       NOT NULL DEFAULT 10      COMMENT '该时段最大挂号数',
    `status`       TINYINT   NOT NULL DEFAULT 1       COMMENT '状态：0=停诊 / 1=可预约',
    `created_at`   DATETIME  NOT NULL                 COMMENT '创建时间',
    `updated_at`   DATETIME  NOT NULL                 COMMENT '修改时间',
    PRIMARY KEY (`id`),
    KEY `idx_doctor_date` (`doctor_id`, `work_date`),
    CONSTRAINT `fk_schedule_doctor` FOREIGN KEY (`doctor_id`) REFERENCES `doctor` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='医生排班表';

-- ============================================================
-- 5. 病人表
--   软删除策略：deleted_at（病人注销后其历史就诊数据必须依法保留）
-- ============================================================
CREATE TABLE `patient` (
    `id`              BIGINT       NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `user_id`         BIGINT       NOT NULL                 COMMENT '用户ID（一对一）',
    `gender`          TINYINT                               COMMENT '性别：0=未知 / 1=男 / 2=女',
    `birth_date`      DATE                                  COMMENT '出生日期',
    `address`         VARCHAR(255)                          COMMENT '居住地址',
    `blood_type`      VARCHAR(10)                           COMMENT '血型',
    `allergy_history` VARCHAR(500)                          COMMENT '过敏史',
    `deleted_at`      DATETIME                              COMMENT '软删除时间（NULL=正常）',
    `created_at`      DATETIME     NOT NULL                 COMMENT '创建时间',
    `updated_at`      DATETIME     NOT NULL                 COMMENT '修改时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_id` (`user_id`),
    CONSTRAINT `fk_patient_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='病人表';

-- ============================================================
-- 6. 药品表
--   软删除策略：deleted_at（药品停产后历史处方明细的药品引用不能断链）
-- ============================================================
CREATE TABLE `drug` (
    `id`            BIGINT        NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `name`          VARCHAR(100)  NOT NULL                 COMMENT '名称',
    `specification` VARCHAR(50)                            COMMENT '规格，如 0.25g/片',
    `unit`          VARCHAR(20)                            COMMENT '单位，如 盒/瓶/支',
    `price`         DECIMAL(10,2) NOT NULL                 COMMENT '单价',
    `stock`         INT           NOT NULL                 COMMENT '库存数量',
    `manufacturer`  VARCHAR(100)                           COMMENT '生产厂商',
    `deleted_at`    DATETIME                               COMMENT '软删除时间（NULL=正常）',
    `created_at`    DATETIME      NOT NULL                 COMMENT '创建时间',
    `updated_at`    DATETIME      NOT NULL                 COMMENT '修改时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='药品表';

-- ============================================================
-- 7. 挂号表
--   软删除策略：不使用 deleted_at，通过 status=0（已取消）实现
--   病人选择科室 → 选择医生 → 挂号
--   一个医生可被多人挂号，一个病人可挂多次号
-- ============================================================
CREATE TABLE `appointment` (
    `id`               BIGINT    NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `patient_id`       BIGINT    NOT NULL                 COMMENT '病人ID',
    `doctor_id`        BIGINT    NOT NULL                 COMMENT '医生ID',
    `department_id`    BIGINT    NOT NULL                 COMMENT '科室ID（冗余自 doctor，方便按科室直接查挂号）',
    `appointment_time` DATETIME                           COMMENT '预约就诊时间',
    `status`           TINYINT   NOT NULL DEFAULT 1       COMMENT '状态：0=已取消 / 1=待就诊 / 2=已就诊',
    `created_at`       DATETIME  NOT NULL                 COMMENT '创建时间',
    `updated_at`       DATETIME  NOT NULL                 COMMENT '修改时间',
    PRIMARY KEY (`id`),
    KEY `idx_patient_id` (`patient_id`),
    KEY `idx_doctor_id` (`doctor_id`),
    KEY `idx_department_id` (`department_id`),
    CONSTRAINT `fk_appointment_patient` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`id`),
    CONSTRAINT `fk_appointment_doctor` FOREIGN KEY (`doctor_id`) REFERENCES `doctor` (`id`),
    CONSTRAINT `fk_appointment_department` FOREIGN KEY (`department_id`) REFERENCES `department` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='挂号表';

-- ============================================================
-- 8. 诊断记录表
--   软删除策略：不加任何删除机制。医疗记录依法不可删除
--   挂号（已就诊）后由医生填写，一次挂号对应一条诊断记录
--   doctor_id / patient_id 冗余自 appointment，方便直接按医生/病人查询诊断历史
-- ============================================================
CREATE TABLE `diagnosis_record` (
    `id`                  BIGINT       NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `appointment_id`      BIGINT       NOT NULL                 COMMENT '挂号ID（一对一）',
    `doctor_id`           BIGINT       NOT NULL                 COMMENT '医生ID（冗余，方便按医生查诊断历史）',
    `patient_id`          BIGINT       NOT NULL                 COMMENT '病人ID（冗余，方便按病人查诊断历史）',
    `chief_complaint`     VARCHAR(500)                          COMMENT '主诉，如"头痛3天"',
    `diagnosis_result`    VARCHAR(500)                          COMMENT '诊断结果',
    `prescription_advice` VARCHAR(500)                          COMMENT '医嘱',
    `created_at`          DATETIME     NOT NULL                 COMMENT '创建时间',
    `updated_at`          DATETIME     NOT NULL                 COMMENT '修改时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_appointment_id` (`appointment_id`),
    KEY `idx_doctor_id` (`doctor_id`),
    KEY `idx_patient_id` (`patient_id`),
    CONSTRAINT `fk_diagnosis_appointment` FOREIGN KEY (`appointment_id`) REFERENCES `appointment` (`id`),
    CONSTRAINT `fk_diagnosis_doctor` FOREIGN KEY (`doctor_id`) REFERENCES `doctor` (`id`),
    CONSTRAINT `fk_diagnosis_patient` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='诊断记录表';

-- ============================================================
-- 9. 处方表
--   软删除策略：不加任何删除机制。处方一旦开具不可撤回
--   一次诊断产生一张处方，一张处方对应多个药品明细
--   一张处方对应一笔药品订单
-- ============================================================
CREATE TABLE `prescription` (
    `id`            BIGINT    NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `diagnosis_id`  BIGINT    NOT NULL                 COMMENT '诊断记录ID（一对一）',
    `doctor_id`     BIGINT    NOT NULL                 COMMENT '医生ID（冗余，方便按医生查处方）',
    `patient_id`    BIGINT    NOT NULL                 COMMENT '病人ID（冗余，方便按病人查处方）',
    `created_at`    DATETIME  NOT NULL                 COMMENT '创建时间',
    `updated_at`    DATETIME  NOT NULL                 COMMENT '修改时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_diagnosis_id` (`diagnosis_id`),
    KEY `idx_doctor_id` (`doctor_id`),
    KEY `idx_patient_id` (`patient_id`),
    CONSTRAINT `fk_prescription_diagnosis` FOREIGN KEY (`diagnosis_id`) REFERENCES `diagnosis_record` (`id`),
    CONSTRAINT `fk_prescription_doctor` FOREIGN KEY (`doctor_id`) REFERENCES `doctor` (`id`),
    CONSTRAINT `fk_prescription_patient` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='处方表';

-- ============================================================
-- 10. 处方明细表
--   软删除策略：不加删除机制。随处方存在，无独立删除场景
--   一张处方包含多种药品，一种药品可出现在多张处方中（多对多中间表）
-- ============================================================
CREATE TABLE `prescription_item` (
    `id`              BIGINT       NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `prescription_id` BIGINT       NOT NULL                 COMMENT '处方ID',
    `drug_id`         BIGINT       NOT NULL                 COMMENT '药品ID',
    `quantity`        INT          NOT NULL                 COMMENT '数量',
    `usage_method`    VARCHAR(100)                          COMMENT '用法，如"一日三次，一次一片"',
    `days`            INT                                   COMMENT '天数',
    `created_at`      DATETIME     NOT NULL                 COMMENT '创建时间',
    `updated_at`      DATETIME     NOT NULL                 COMMENT '修改时间',
    PRIMARY KEY (`id`),
    KEY `idx_prescription_id` (`prescription_id`),
    KEY `idx_drug_id` (`drug_id`),
    CONSTRAINT `fk_item_prescription` FOREIGN KEY (`prescription_id`) REFERENCES `prescription` (`id`),
    CONSTRAINT `fk_item_drug` FOREIGN KEY (`drug_id`) REFERENCES `drug` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='处方明细表';

-- ============================================================
-- 11. 药品订单表
--   软删除策略：不使用 deleted_at，通过 status=0（已取消）实现
--   一张处方对应一笔药品订单，病人可查询自己所有的药品订单
-- ============================================================
CREATE TABLE `drug_order` (
    `id`              BIGINT        NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `prescription_id` BIGINT        NOT NULL                 COMMENT '处方ID（一对一）',
    `total_amount`    DECIMAL(10,2)                          COMMENT '总金额',
    `status`          TINYINT       NOT NULL DEFAULT 1       COMMENT '状态：0=已取消 / 1=待取药 / 2=已取药',
    `created_at`      DATETIME      NOT NULL                 COMMENT '创建时间',
    `updated_at`      DATETIME      NOT NULL                 COMMENT '修改时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_prescription_id` (`prescription_id`),
    CONSTRAINT `fk_order_prescription` FOREIGN KEY (`prescription_id`) REFERENCES `prescription` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='药品订单表';

-- ============================================================
-- 初始化数据：默认科室、管理员账户、医生账户
-- ============================================================

-- 默认科室（医生注册时必须归属科室）
INSERT INTO `department` (`name`, `description`, `created_at`, `updated_at`)
VALUES ('内科', '默认科室，涵盖常见内科疾病', NOW(), NOW());

-- 管理员账户（role=0）
INSERT INTO `user` (`password`, `name`, `email`, `phone`, `role`, `status`, `created_at`, `updated_at`)
VALUES (
    '$2b$12$W0kzir89l063NIvzLnCQbuyVUg5Q7.mNAgYaOqJLcj7wjXz4HdIh6',
    '管理员',
    'admin@medflow.com',
    NULL,
    0,
    1,
    NOW(),
    NOW()
);

-- 医生账户（role=1）
INSERT INTO `user` (`password`, `name`, `email`, `phone`, `role`, `status`, `created_at`, `updated_at`)
VALUES (
    '$2b$12$GLOtf6e1qAEnk00bI85N2eKXrFtRfM6wG.voU0/rFUqSLGYiygtHu',
    '医生1',
    'doctor1@medflow.com',
    NULL,
    1,
    1,
    NOW(),
    NOW()
);

-- 医生详细信息（关联 user 表与 department 表）
INSERT INTO `doctor` (`user_id`, `department_id`, `title`, `introduction`, `created_at`, `updated_at`)
SELECT u.id, d.id, '主治医师', '默认医生账户', NOW(), NOW()
FROM `user` u, `department` d
WHERE u.email = 'doctor1@medflow.com' AND d.name = '内科';
