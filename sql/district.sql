-- v2.0
-- 1. 区县表
CREATE TABLE IF NOT EXISTS districts (
    district_id INT PRIMARY KEY AUTO_INCREMENT,
    circle_id INT COMMENT '圈层',
    district_name VARCHAR(32) NOT NULL COMMENT '区县名字',
    simple_name VARCHAR(32) NOT NULL COMMENT '区县简称',
    UNIQUE KEY unique_district_name (district_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. 分类表
CREATE TABLE IF NOT EXISTS categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(32) NOT NULL,
    UNIQUE KEY unique_category_name (category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 3. 考核类型表
CREATE TABLE IF NOT EXISTS evaluation_types (
    type_id INT PRIMARY KEY AUTO_INCREMENT,
    type_name VARCHAR(64) NOT NULL,
    UNIQUE KEY unique_type_name (type_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 专业表
CREATE TABLE IF NOT EXISTS majors (
    major_id INT PRIMARY KEY AUTO_INCREMENT,
    major_code VARCHAR(10) NOT NULL,
    major_name VARCHAR(100) NOT NULL,
    UNIQUE KEY unique_major_code (major_code),
    UNIQUE KEY unique_major_name (major_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. KPI类型表
CREATE TABLE IF NOT EXISTS kpi_types (
    kpi_type_id INT PRIMARY KEY AUTO_INCREMENT,
    kpi_type VARCHAR(64) COMMENT 'kpi类型'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. 日期维度表
CREATE TABLE IF NOT EXISTS dim_date (
  day DATE PRIMARY KEY,
  year SMALLINT,
  quarter TINYINT,
  month TINYINT,
  day_of_month TINYINT,
  iso_year SMALLINT,
  iso_week TINYINT,
  dow TINYINT,
  is_weekend TINYINT,
  is_holiday TINYINT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. 指标表（修正CHECK+COMMENT语法，适配5.7）
CREATE TABLE IF NOT EXISTS indicator (
    indicator_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    indicator_code VARCHAR(20) UNIQUE NOT NULL COMMENT '指标编码',
    indicator_name VARCHAR(100) NOT NULL COMMENT '指标名称',
    unit VARCHAR(20) COMMENT '单位，如%, 次, 用户数',
    -- 维度外键（逻辑外键）
    category_id    INT NULL COMMENT '分类ID（categories）',
    major_id       INT NULL COMMENT '专业ID（majors）',
    type_id        INT NULL COMMENT '类型ID（evaluation_types）',
    kpi_type_id    INT NULL COMMENT 'KPI类型ID（kpi_types）',
    -- 修正：将CHECK逻辑合并到COMMENT，移除CHECK后的COMMENT
    is_positive TINYINT NOT NULL COMMENT '是否正向指标或者逆向指标,1.正向、0.负向、2.其他（仅支持0/1/2）',
    -- 管理属性
    data_owner     VARCHAR(50)  NULL COMMENT '对应数据人',
    data_dept      VARCHAR(50)  NULL COMMENT '对应部门',
    description    VARCHAR(255) NULL COMMENT '指标说明',
    status         TINYINT NOT NULL DEFAULT 1 COMMENT '1启用 0停用',
    version        TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '口径版本',
    create_time    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- 索引
    INDEX ix_indicator_category_id (category_id),
    INDEX ix_indicator_type_id (type_id),
    INDEX ix_indicator_major_id (major_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. 指标数据表（修正CHECK+COMMENT语法，适配5.7）
CREATE TABLE IF NOT EXISTS indicator_data_v2 (
    id           BIGINT AUTO_INCREMENT COMMENT '主键',
    indicator_id INT NOT NULL COMMENT '指标ID，关联 indicator（逻辑外键）',
    indicator_name VARCHAR(100) NOT NULL COMMENT '指标名称',
    -- 修正：合并CHECK逻辑到COMMENT，移除非法语法
    type_id        INT NULL COMMENT '类型ID（evaluation_types）',
    major_id       INT NULL COMMENT '专业ID（majors）',
    is_positive TINYINT NOT NULL COMMENT '是否正向指标或者逆向指标,1.正向、0.负向、2.其他（仅支持0/1/2）',
    circle_id    INT NOT NULL COMMENT '圈层ID，关联 districts.circle_id',
    district_id  INT NOT NULL COMMENT '区县ID，关联 districts（逻辑外键）',
    district_name VARCHAR(32) NOT NULL COMMENT '区县名字',
    stat_date    DATE NOT NULL COMMENT '统计日期',
    value        DECIMAL(18,4) NULL COMMENT '指标值',
    benchmark    DECIMAL(18,4) NULL COMMENT '基准值',
    challenge    DECIMAL(18,4) NULL COMMENT '挑战值',
    exemption    DECIMAL(18,4) NULL COMMENT '豁免值',
    zero_tolerance DECIMAL(18,4) NULL COMMENT '零容忍值',
    score        DECIMAL(18,4) NULL COMMENT '得分',
    create_time  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    PRIMARY KEY (id, stat_date),
    UNIQUE KEY uk_circle_did_iid_date (circle_id, district_id, indicator_id, stat_date),
    KEY ix_circle_iid_date (circle_id, indicator_id, stat_date, district_id),
    KEY ix_iid_date (indicator_id, stat_date, circle_id, district_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;