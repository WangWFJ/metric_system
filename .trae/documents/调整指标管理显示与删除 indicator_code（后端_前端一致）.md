## 目标
- 列表显示指标名称；第一列为 indicator_id；“专业”“类型”显示中文名称；正向列名为“是否正向”。
- 删除后端/前端对 indicator_code 的全部依赖与使用。

## 后端改造
### ORM/Schema
- 修改 models.metrics.Indicator：删除字段 indicator_code；保留 indicator_name、major_id、type_id、is_positive、status、version 等。
- 若存在任意唯一约束依赖 indicator_code，改为按 indicator_id（主键）维持唯一。

### Pydantic 模型
- 调整 IndicatorBase/IndicatorOut：移除 indicator_code 字段；其它字段不变。

### 服务层
- create_indicator/update_indicator：不再设置/校验 indicator_code。
- list_indicators：支持 q 按 indicator_name 模糊；联接 majors、evaluation_types 返回中文名（新增字段 major_name、type_name）。
- 其他函数中关于去重的窗口函数：之前按 indicator_code 分组；改为按 indicator_id 或按 indicator_name（若存在版本语义），默认使用 indicator_id 分组。

### 路由/API
- /api/v1/metrics/indicators：响应中增加中文名（major_name、type_name），移除 indicator_code；查询参数 q 仅作用于 indicator_name。
- /indicators/{id} 的 create/update：请求体不含 indicator_code；状态校验限制 0/1（在服务层与 Pydantic 校验）。
- 代码引用中所有 indicator_code 条件（如 metrics_query/snapshot 中筛选）全部删除或替换为 indicator_id/indicator_name。

## 前端改造
### API 类型
- IndicatorFull/IndicatorSimple 去除 indicator_code；为 IndicatorFull 增加 major_name、type_name 可选字段。
- listIndicators/createIndicator/updateIndicator 删除 code 相关属性；查询入参 q 仅按名称。

### 指标管理页
- 表格列：第一列 indicator_id；显示 indicator_name、unit、major_name、type_name、是否正向、状态、操作。
- 列名“正向”改为“是否正向”。
- 表单：移除编码输入；保留名称、单位、专业/类型下拉（中文），正向下拉（0/1/2），状态下拉限制 0/1；提交时仅携带对应 ID（major_id、type_id），不含 indicator_code。
- 下拉数据来源沿用 /metrics/majors 和 /metrics/evaluation_types。

## 关联修改
- 搜索接口 /indicators/search：删除对 indicator_code 的匹配，保留名称匹配；若前端未用到，可直接废弃或返回兼容。
- 其他页面若展示到 indicator_code（例如简单下拉），统一改为用 indicator_name 与 indicator_id。

## 验证
- 新增、编辑、删除指标成功；状态仅能为 0/1；列表显示中文“专业”“类型”，列名为“是否正向”。
- 运行趋势/查询接口，确保去除 indicator_code 后逻辑正常（按 indicator_id/名称筛选）。

## 迁移说明
- 若数据库已删除 indicator_code 列：ORM 同步后端即可；若历史代码中仍有引用，全部移除。

## 交付
- 提交后端服务与前端视图的联动改造；自测通过后再交付。