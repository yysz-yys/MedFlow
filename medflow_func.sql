-- ============================================================
-- 网上医疗记录系统（云诊易 MedFlow）— 功能辅助表
-- 说明：这些表与核心业务（挂号/诊断/处方）不直接关联，
--       属于系统运行必需的支撑表
-- ============================================================

CREATE DATABASE IF NOT EXISTS medflow
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE medflow;
-- ============================================================
-- F1. 操作日志表
-- 用途：记录系统中所有关键操作，满足医疗系统合规与审计要求
-- 写入方：后端中间件/装饰器，业务代码无需手动调用
-- 清理策略：建议保留至少 3 年，可按年归档
-- 注意：不设外键到 user 表，避免用户被软删除后日志断链；
--       改为冗余存 user_id + user_name 两条字段
-- ============================================================
CREATE TABLE `audit_log` (
    `id`            BIGINT       NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `user_id`       BIGINT                                COMMENT '操作人ID（冗余，无外键）',
    `user_name`     VARCHAR(50)                           COMMENT '操作人姓名（冗余，方便直接查看）',
    `role`          TINYINT                               COMMENT '操作人角色：0=管理员 / 1=医生 / 2=病人',
    `action`        VARCHAR(50)  NOT NULL                 COMMENT '操作类型，如 LOGIN_SUCCESS / CREATE_DIAGNOSIS',
    `target_type`   VARCHAR(50)                           COMMENT '操作对象类型，如 appointment / diagnosis_record',
    `target_id`     BIGINT                                COMMENT '操作对象ID',
    `old_value`     VARCHAR(500)                          COMMENT '修改前的值（JSON），如 {"stock":100}；新增操作填 NULL',
    `new_value`     VARCHAR(500)                          COMMENT '修改后的值（JSON），如 {"stock":80}；删除操作填 NULL',
    `detail`        VARCHAR(500)                          COMMENT '操作详情，如 "病人张三挂了内科王医生的号"',
    `ip_address`    VARCHAR(45)                           COMMENT '操作IP',
    `created_at`    DATETIME     NOT NULL                 COMMENT '操作时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_action` (`action`),
    KEY `idx_target` (`target_type`, `target_id`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- ============================================================
-- action 操作类型枚举（必须记录的全部操作）
-- 命名规范：{动词}_{对象}，动词取 CREATE/UPDATE/DELETE/CANCEL/
--           VIEW/DISPENSE 等
--
-- 总原则：以下操作一经发生，必须写入 audit_log，不论操作人角色。
--        管理员、医生、病人同等对待，无豁免。
-- ============================================================
--
-- 【第一类：认证安全】
--   LOGIN_SUCCESS             登录成功
--   LOGIN_FAILED              登录失败
--   CHANGE_PASSWORD           修改密码
--   DISABLE_USER              管理员禁用用户
--   ENABLE_USER               管理员启用用户
--
-- 【第二类：写操作 — 科室】
--   CREATE_DEPARTMENT         新增科室
--   UPDATE_DEPARTMENT         编辑科室
--   DELETE_DEPARTMENT         软删除科室
--
-- 【第二类：写操作 — 医生】
--   CREATE_DOCTOR             新增医生
--   UPDATE_DOCTOR             编辑医生
--   DELETE_DOCTOR             软删除医生
--
-- 【第二类：写操作 — 病人】
--   CREATE_PATIENT            新增病人（注册时自动创建）
--   UPDATE_PATIENT            编辑病人信息
--   DELETE_PATIENT            软删除病人（注销）
--
-- 【第二类：写操作 — 药品】
--   CREATE_DRUG               新增药品
--   UPDATE_DRUG               编辑药品信息
--   DELETE_DRUG               软删除药品
--   UPDATE_DRUG_STOCK         调整库存（old_value/new_value 记录 stock 变化）
--
-- 【第二类：写操作 — 挂号】
--   CREATE_APPOINTMENT        病人挂号
--   UPDATE_APPOINTMENT        病人修改挂号（改时间/改医生/改科室）
--   CANCEL_APPOINTMENT        病人取消挂号
--
-- 【第二类：写操作 — 诊断】
--   CREATE_DIAGNOSIS          医生填写诊断记录
--   UPDATE_DIAGNOSIS          医生修改诊断记录（允许修改，操作日志保留原始值）
--
-- 【第二类：写操作 — 处方】
--   CREATE_PRESCRIPTION       医生开具处方（含多条药品明细）
--   UPDATE_PRESCRIPTION       医生修改处方（仅限对应订单未取药时允许；
--                             prescription_item 先删后插，操作日志记录变更）
--
-- 【第二类：写操作 — 排班】
--   CREATE_SCHEDULE           管理员设置医生排班
--   UPDATE_SCHEDULE           修改排班（改时间/时段/限号数）
--   DELETE_SCHEDULE           删除排班或标记停诊

-- 【第二类：写操作 — 文件】
--   UPLOAD_FILE               上传附件（检查报告/诊断附件）
--   DELETE_FILE               删除附件

-- 【第二类：写操作 — 订单】
--   CANCEL_DRUG_ORDER         取消药品订单（退还库存）

-- 注：药品订单随处方自动生成并扣减库存，不产生独立的 action；
--     订单生成记录包含在 CREATE_PRESCRIPTION 的 new_value 中。
--
-- 【第三类：隐私访问】
--   VIEW_DIAGNOSIS            查看诊断记录（医生看病人/管理员查病历/病人看自己）
--   VIEW_PRESCRIPTION         查看处方记录（同上，含管理员审查）
--   VIEW_DRUG_ORDER           查看药品订单（同上，含管理员审查）
--
-- 【不记录】
--   查询列表、页面刷新、无敏感数据的 GET 请求
--
-- old_value / new_value 使用规则：
--   新增操作：old_value=NULL,  new_value=新增数据的JSON
--   编辑操作：old_value=修改前JSON, new_value=修改后JSON
--   删除/取消：old_value=被删数据JSON, new_value=NULL
--
-- 示例：管理员将阿莫西林库存从100调为80
--   action=UPDATE_DRUG_STOCK
--   old_value={"stock":100}  new_value={"stock":80}

-- ============================================================
-- F2. 验证码表
-- 用途：存储注册/登录/找回密码等场景的短信或邮箱验证码
-- 写入方：发送验证码接口写入，校验接口读取并删除
-- 清理策略：定时任务清理过期的（expires_at < NOW()）记录
-- ============================================================
CREATE TABLE `verification_code` (
    `id`             BIGINT       NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `target`         VARCHAR(100) NOT NULL                 COMMENT '接收方（手机号或邮箱）',
    `code`           VARCHAR(10)  NOT NULL                 COMMENT '验证码（6位数字）',
    `scene`          VARCHAR(30)  NOT NULL                 COMMENT '使用场景：REGISTER / LOGIN / RESET_PASSWORD',
    `send_ip`        VARCHAR(45)                           COMMENT '发送请求的IP（用于防刷风控）',
    `attempt_count`  TINYINT      NOT NULL DEFAULT 0       COMMENT '校验失败次数（连续输错3次即作废）',
    `expires_at`     DATETIME     NOT NULL                 COMMENT '过期时间，如发送后5分钟',
    `used`           TINYINT      NOT NULL DEFAULT 0       COMMENT '是否已使用：0=未使用 / 1=已使用',
    `created_at`     DATETIME     NOT NULL                 COMMENT '发送时间',
    PRIMARY KEY (`id`),
    KEY `idx_target_scene` (`target`, `scene`),
    KEY `idx_expires_at` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='验证码表';

-- ============================================================
-- F3. 系统配置表
-- 用途：集中管理系统级别的开关和参数，避免硬编码到代码中
-- 写入方：管理员通过后端管理页面或直接操作数据库修改
-- 缓存策略：后端启动时加载到内存，修改后刷新缓存
-- ============================================================
CREATE TABLE `system_config` (
    `id`           BIGINT       NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `config_key`   VARCHAR(100) NOT NULL                 COMMENT '配置键，如 default_appointment_slots',
    `config_value` VARCHAR(500)                          COMMENT '配置值，如 "08:00,10:00,14:00,16:00"',
    `description`  VARCHAR(255)                          COMMENT '说明，如 "默认挂号时段配置"',
    `created_at`   DATETIME     NOT NULL                 COMMENT '创建时间',
    `updated_at`   DATETIME     NOT NULL                 COMMENT '修改时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_config_key` (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- ============================================================
-- F4. 数据字典表
-- 用途：统一管理系统中所有 TINYINT 枚举的含义
--       前端/后端通过 dict_type + dict_key 查询显示文本
-- 写入方：系统初始化时批量 INSERT，后续新增枚举值追加即可
-- ============================================================
CREATE TABLE `data_dict` (
    `id`          BIGINT       NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `dict_type`   VARCHAR(50)  NOT NULL                 COMMENT '字典类型，如 user_role / appointment_status',
    `dict_key`    TINYINT      NOT NULL                 COMMENT '枚举值，如 0 / 1 / 2',
    `dict_label`  VARCHAR(50)  NOT NULL                 COMMENT '显示文本，如 "管理员" / "已取消"',
    `sort_order`  INT          NOT NULL DEFAULT 0       COMMENT '排序（同类型内数字小的排前面）',
    `created_at`  DATETIME     NOT NULL                 COMMENT '创建时间',
    `updated_at`  DATETIME     NOT NULL                 COMMENT '修改时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_type_key` (`dict_type`, `dict_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据字典表';

-- ---------------------------------------------------------
-- 数据字典初始化数据
-- ---------------------------------------------------------
INSERT INTO `data_dict` (`dict_type`, `dict_key`, `dict_label`, `sort_order`, `created_at`, `updated_at`) VALUES
('user_role', 0, '管理员', 0, NOW(), NOW()),
('user_role', 1, '医生',   1, NOW(), NOW()),
('user_role', 2, '病人',   2, NOW(), NOW()),
('user_status', 0, '禁用', 0, NOW(), NOW()),
('user_status', 1, '正常', 1, NOW(), NOW()),
('gender', 0, '未知', 0, NOW(), NOW()),
('gender', 1, '男',   1, NOW(), NOW()),
('gender', 2, '女',   2, NOW(), NOW()),
('appointment_status', 0, '已取消', 0, NOW(), NOW()),
('appointment_status', 1, '待就诊', 1, NOW(), NOW()),
('appointment_status', 2, '已就诊', 2, NOW(), NOW()),
('drug_order_status', 0, '已取消', 0, NOW(), NOW()),
('drug_order_status', 1, '待取药', 1, NOW(), NOW()),
('drug_order_status', 2, '已取药', 2, NOW(), NOW()),
('yes_no', 0, '否', 0, NOW(), NOW()),
('yes_no', 1, '是', 1, NOW(), NOW());

-- ---------------------------------------------------------
-- 系统配置初始化数据
-- ---------------------------------------------------------
INSERT INTO `system_config` (`config_key`, `config_value`, `description`, `created_at`, `updated_at`) VALUES
('default_appointment_slots', '08:00,10:00,14:00,16:00', '每天可预约时段', NOW(), NOW()),
('max_appointments_per_day', '50', '每位医生每日最大挂号数', NOW(), NOW()),
('appointment_cancel_window_hours', '2', '距预约几小时内不可取消', NOW(), NOW()),
('prescription_edit_window_hours', '24', '处方开具后几小时内可修改', NOW(), NOW());

-- ============================================================
-- F5. 令牌黑名单表
-- 用途：用户登出后将 JWT 的 jti 写入此表，后续请求校验时判断 token 是否
--       已被拉黑，非黑名单则放行。解决 JWT 无状态登出的问题。
-- 清理策略：定时任务清理 expires_at 已过期的记录
-- ============================================================
CREATE TABLE `token_blacklist` (
    `id`         BIGINT       NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `token_jti`  VARCHAR(100) NOT NULL                 COMMENT 'JWT 的 jti 声明值（唯一标识一个 token）',
    `user_id`    BIGINT       NOT NULL                 COMMENT '所属用户ID',
    `expires_at` DATETIME     NOT NULL                 COMMENT 'token 原始过期时间（过期后可清理）',
    `created_at` DATETIME     NOT NULL                 COMMENT '拉黑时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_token_jti` (`token_jti`),
    KEY `idx_expires_at` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='令牌黑名单表';

-- ============================================================
-- F6. 文件附件表
-- 用途：病人上传检查报告/影像，医生上传诊断附件
-- 存储策略：文件存本地磁盘，数据库只记录路径和元信息
-- 文件类型限制：仅允许图片（jpg/png/gif/webp）和视频（mp4/avi/mov）
--             校验在应用层执行，数据库不设 CHECK 约束
-- ============================================================
CREATE TABLE `file_attachment` (
    `id`            BIGINT        NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `uploader_id`   BIGINT        NOT NULL                 COMMENT '上传人ID',
    `uploader_role` TINYINT       NOT NULL                 COMMENT '上传人角色（取值同 user_role 字典）：0=管理员 / 1=医生 / 2=病人',
    `related_type`  VARCHAR(50)   NOT NULL                 COMMENT '关联对象类型，如 diagnosis_record / prescription',
    `related_id`    BIGINT        NOT NULL                 COMMENT '关联对象ID',
    `file_name`     VARCHAR(255)  NOT NULL                 COMMENT '原始文件名',
    `file_path`     VARCHAR(500)  NOT NULL                 COMMENT '存储路径',
    `file_size`     BIGINT                                  COMMENT '文件大小（字节）',
    `file_type`     VARCHAR(100)                           COMMENT 'MIME 类型，如 image/png',
    `created_at`    DATETIME      NOT NULL                 COMMENT '上传时间',
    PRIMARY KEY (`id`),
    KEY `idx_related` (`related_type`, `related_id`),
    KEY `idx_uploader` (`uploader_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件附件表';

-- ============================================================
-- F7. 通知消息表
-- 用途：推送系统通知给用户，包括挂号提醒、取药提醒、系统公告等
-- 写入方：后端在关键业务节点自动写入（挂号成功→推送给医生，取药→推送给病人）
-- ============================================================
CREATE TABLE `notification` (
    `id`           BIGINT        NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `user_id`      BIGINT        NOT NULL                 COMMENT '接收人ID',
    `title`        VARCHAR(100)  NOT NULL                 COMMENT '标题，如 "挂号提醒"',
    `content`      VARCHAR(500)  NOT NULL                 COMMENT '内容，如 "张三预约了您2026-07-10 09:00的就诊"',
    `type`         VARCHAR(30)   NOT NULL                 COMMENT '通知分类：APPOINTMENT 挂号通知 / DISPENSE 诊疗取药通知 / SYSTEM 系统公告',
    `is_read`      TINYINT       NOT NULL DEFAULT 0       COMMENT '已读状态：0=未读 / 1=已读',
    `related_type` VARCHAR(50)                            COMMENT '关联对象类型（可选，点击跳转用）',
    `related_id`   BIGINT                                 COMMENT '关联对象ID（可选）',
    `created_at`   DATETIME      NOT NULL                 COMMENT '发送时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_read` (`user_id`, `is_read`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知消息表';

