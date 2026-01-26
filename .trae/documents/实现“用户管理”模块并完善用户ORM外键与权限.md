## 目标
- 在后端加入用户-角色外键关系与角色/权限ORM映射，保证与现有表结构一致。
- 新增“用户管理”模块：仅超级管理员可对用户进行增删改查与锁定/启用。
- 前端侧新增用户管理页面和左侧菜单入口，支持按用户名/手机号搜索、角色筛选、分页、创建/编辑/删除。

## 后端改造
### ORM 与关系
1. User：保持现有字段，新增 role 关系（ForeignKey + relationship）。
2. Role、Permission、RolePermission：新增 ORM 模型（role_id/permission_id 主键与约束一致）。
3. 约束：User.role_id -> roles.role_id（onupdate 无、ondelete 无；与DDL一致）。

### Pydantic 模型
- UserBase：username、phone、role_id、status；Create 额外包含 password；Update 支持部分可选字段。
- UserOut：id、username、phone、role_id、status、role_name/role_code（便于前端显示）。
- RoleOut、PermissionOut 简单列表模型。

### 权限与鉴权
- get_current_user 保持基于 JWT 的 id 解析。
- 新增依赖 require_admin：判定当前用户 role_code=='admin' 或 role_id==1；用于保护用户管理接口。
- 可选：按权限表实现 has_permission('user:manage')；第一期先用 admin 角色即可。

### 用户管理接口
- 路由前缀：/api/v1/user_manage（或 /api/v1/users/admin）。
- GET /users：分页查询，支持 q（用户名/手机号模糊）、role_id、status 筛选；返回 UserOut（含角色中文名）。
- POST /users：创建用户（校验唯一 username；phone 可选；role_id 必填；默认 status=1）。
- PATCH /users/{id}：更新用户（可改 phone/role_id/status；允许重置密码）。
- DELETE /users/{id}：删除用户。
- GET /roles：返回启用角色列表（供前端下拉）。

### 登录兼容
- 已实现“用户名或手机号登录”；保持不变。

## 前端实现
### 路由与菜单
- 左侧“数据管理”并行模块下新增“用户管理”入口（/users）。

### 页面功能（UsersManage.vue）
- 顶部筛选：搜索（用户名/手机号）、角色下拉、状态下拉；查询按钮；新增用户按钮。
- 列表列：ID、用户名、手机号、角色（中文）、状态、创建时间、操作（编辑/删除/锁定/启用）。
- 分页：total、page、size。
- 弹窗表单（新增/编辑）：用户名（新增必填）、手机号、角色下拉、状态、密码（新增必填/编辑可重置）。

### 前端 API
- listUsers({q, role_id, status, page, size})
- createUser(payload)
- updateUser(id, payload)
- deleteUser(id)
- listRoles()

## 安全与校验
- 后端接口均加 require_admin 依赖；返回 403 时前端提示“无权限”。
- 创建/更新校验：username 唯一；role_id 必须存在且启用；status ∈ {0,1}；手机号长度=11（可选）。

## 迁移与兼容
- 不修改现有登录与用户信息接口 /users/me；新增管理接口独立，不影响现有功能。

## 验证
- 使用seed角色数据：admin用户能访问用户管理；viewer/data_entry访问返回403。
- 新增用户后能登录；更改角色/状态即时生效。

## 交付
- 提供后端ORM、路由与服务、前端页面与API；自测通过后提交。