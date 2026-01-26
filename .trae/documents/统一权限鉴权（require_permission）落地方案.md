## 目标
- 为系统所有模块提供统一、规范、可扩展的接口级鉴权机制
- 基于 FastAPI Depends，在路由层显式声明权限依赖
- 权限以 permission_code（resource:action）为准，鉴权失败返回 403

## 后端实现
### 通用依赖与缓存
- 新增依赖函数：require_permission(permission_code: str)
  - 从 JWT 解析当前用户 id（沿用现有 get_current_user）
  - 管理员（role_id==1 或 role_code=='admin'）直接通过
  - 读取并缓存当前用户的权限列表（permission_code 字符串集合）
- 缓存策略
  - 进程内 LRU/TTL 简易缓存（dict[user_id] -> {codes: set[str], expire_ts}，TTL 默认 5 分钟）
  - 每次请求优先命中缓存；过期或未命中时查询数据库并刷新
- 权限加载 SQL
  - JOIN role_permissions -> permissions 过滤 status==1，返回 permission_code 列

### 辅助接口（可选）
- GET /api/v1/users/me/permissions：返回当前用户权限列表，用于前端 UI 控制（缓存同上）

### 路由层声明（覆盖范围）
- 仪表板/查询类
  - GET /api/v1/metrics/series → Depends(require_permission("indicator_data:view"))
  - 若存在指标定义查询：GET /api/v1/metrics/indicators → Depends(require_permission("indicator:view"))
- 指标管理
  - POST /api/v1/metrics/indicators → "indicator:add"
  - PUT  /api/v1/metrics/indicators/{id} → "indicator:edit"
  - DELETE /api/v1/metrics/indicators/{id} → "indicator:delete"
  - 批量上传指标：POST /api/v1/metrics/indicators/upload → "indicator:add"
- 指标数据
  - GET    /api/v1/metrics/series → "indicator_data:view"（已列）
  - POST   /api/v1/metrics/data → "indicator_data:add"
  - PUT/PATCH（如有）→ "indicator_data:edit"
  - DELETE /api/v1/metrics/data → "indicator_data:delete"
  - 数据上传模板/上传：视为新增数据 → "indicator_data:add"
- 用户管理
  - /api/v1/admin/users/** → "user:manage"
  - /api/v1/admin/permissions/** → "user:manage"（权限/角色管理归入用户管理权限）

### 角色约束映射（通过权限自然生效）
- viewer：仅拥有 indicator_data:view → 只能访问仪表板和数据查询接口
- data_entry：indicator_data:view/add/edit/delete → 仅数据增改查删；无 user:manage、indicator:* 权限
- indicator_admin：indicator:* 与 indicator_data:* → 能管指标与数据；无 user:manage
- admin：绕过所有权限检查

### 错误返回
- 鉴权失败统一抛出 HTTPException(403, "Permission denied")
- 禁用/锁定用户（status!=1）在 get_current_user 阶段拒绝

## 前端适配（最小必要）
- 可选：登录后拉取 /users/me/permissions，Pinia 存储，按权限隐藏/禁用 UI 操作
- 示例
  - 无 indicator:add → 隐藏“新增指标”按钮
  - 无 user:manage → 隐藏“用户管理/权限管理/角色管理”菜单

## 代码改动点
- app/core/security.py：新增 require_permission、用户权限缓存、get_user_permissions()
- app/api/endpoints/*：在对应路由上添加 Depends(require_permission(...))
- app/api/endpoints/users.py：可选新增 /me/permissions 接口；现有 require_admin 不变

## 可测试用例
- 四类角色分别登录：访问覆盖范围内各接口，断言 200/403
- 修改角色权限后，缓存 TTL 内强制刷新（可在管理端变更后删除缓存条目），再次访问行为更新

## 交付
- 后端：依赖函数与路由声明全部生效，覆盖目标接口；错误码一致
- 前端：可选 UI 控制；不影响现有功能

确认后将开始落地实现，逐一在后端路由添加权限依赖并提供可选的前端权限感知。