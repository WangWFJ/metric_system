CREATE TABLE `roles` (
  `role_id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '角色ID',
  `role_code` VARCHAR(32) UNIQUE COMMENT '角色编码：admin / viewer',
  `role_name` VARCHAR(64) COMMENT '角色名称',
  `status` TINYINT DEFAULT 1 COMMENT '1启用 0禁用',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

CREATE TABLE `permissions` (
  `permission_id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '权限ID',
  `permission_code` VARCHAR(128) UNIQUE COMMENT '权限编码 indicator:view',
  `permission_name` VARCHAR(128) COMMENT '权限名称',
  `resource` VARCHAR(64) COMMENT '资源 indicator / user / report',
  `action` VARCHAR(32) COMMENT '动作 view / edit / add / delete',
  `status` TINYINT DEFAULT 1 COMMENT '1启用 0禁用',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='权限表';

CREATE TABLE `role_permissions` (
  `role_id` INT NOT NULL COMMENT '角色ID',
  `permission_id` INT NOT NULL COMMENT '权限ID',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`role_id`, `permission_id`),
  CONSTRAINT fk_rp_role FOREIGN KEY (`role_id`) REFERENCES `roles`(`role_id`) ON DELETE CASCADE,
  CONSTRAINT fk_rp_permission FOREIGN KEY (`permission_id`) REFERENCES `permissions`(`permission_id`) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='角色-权限关联表';

CREATE TABLE `user` (
    `id` int PRIMARY KEY AUTO_INCREMENT COMMENT '主键，自增',
    `username` varchar(32) UNIQUE COMMENT '用户名，唯一',
    `password` varchar(128) COMMENT '密码',
    `phone` varchar(11) COMMENT '手机号',
    `role_id` INT COMMENT '角色ID，外键，关联角色表',
    `status` int DEFAULT 1 COMMENT '账号状态，1正常 0锁定',
    `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后修改时间',
    CONSTRAINT fk_user_role FOREIGN KEY (`role_id`) REFERENCES `roles`(`role_id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户信息表';

INSERT INTO roles (role_code, role_name) VALUES
('admin', '超级管理员'),
('indicator_admin', '指标管理员'),
('data_entry', '数据录入员'),
('viewer', '查看者');

INSERT INTO permissions (permission_code, permission_name, resource, action) VALUES
('indicator:view','指标查询','indicator', 'view'),
('indicator:add','指标新增','indicator', 'add'),
('indicator:edit','指标编辑','indicator', 'edit'),
('indicator:delete','指标删除','indicator', 'delete'),
('indicator_data:view', '指标数据查看', 'indicator_data', 'view'),
('indicator_data:add', '指标数据新增', 'indicator_data', 'add'),
('indicator_data:edit', '指标数据修改', 'indicator_data', 'edit'),
('indicator_data:delete','指标数据删除','indicator_data', 'delete'),
('user:manage', '用户管理', 'user', 'manage');

-- 管理员
INSERT INTO role_permissions (role_id, permission_id) VALUES
(1, 1),
(1, 2),
(1, 3),
(1, 4),
(1, 5),
(1, 6),
(1, 7),
(1, 8),
(1, 9);


-- 数据录入
INSERT INTO role_permissions (role_id, permission_id) VALUES
(2, 1),
(2, 2),
(2, 3),
(2, 4),
(2, 5),
(2, 6),
(2, 7),
(2, 8);

-- 数据录入员
INSERT INTO role_permissions (role_id, permission_id)VALUES
(3, 5),
(3, 6),
(3, 7),
(3, 8);

-- 查看者
INSERT INTO role_permissions (role_id, permission_id)VALUES
(4, 5);