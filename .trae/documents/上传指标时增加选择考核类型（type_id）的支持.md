## 背景
- 现有手动上传表单已支持选择“指标、区县、日期、数值”，但未显式选择“考核类型”。
- 数据源已迁移到 indicator_data_v2，表中包含 type_id、major_id 字段，需要在上传时正确写入。

## 前端改造（表单上传）
- 在仪表板的上传对话框中新增“考核类型”下拉选择（type_id）。
  - 数据来源：/api/v1/metrics/evaluation_types（已存在）
  - 绑定 uploadForm.type_id，必填校验
- 提交时将 type_id 一并传给创建接口。
  - 修改处：前端创建数据调用 [indicator.ts](file:///g:/Project/data_proj_v1_trae/frontend/src/api/indicator.ts) 的 createIndicatorData 传入 {type_id}
  - 表单位置：Dashboard.vue 上传对话框 [Dashboard.vue](file:///g:/Project/data_proj_v1_trae/frontend/src/views/Dashboard.vue)

## 后端改造（手动上传）
- 扩展创建请求模型 IndicatorDataCreate，新增可选字段 type_id（与 v2 对齐）。
  - 修改处： [metrics_schemas.py](file:///g:/Project/data_proj_v1_trae/app/models/metrics_schemas.py)
- 在 create_indicator_data 中：
  - 若传入 type_id，则直接写入 v2；
  - 若未传入，则从 Indicator 读取 indicator.type_id 回填；
  - 若传入与 Indicator.type_id 不一致，返回 400（或以 Indicator 为准进行矫正，建议严格检查防止分类混乱）。
  - 始终同时写入 major_id（从 Indicator 读取）以保持反规范化一致性。
  - 写入目标：IndicatorDataV2（现已切换）。
  - 修改处： [indicator_service.py:create_indicator_data](file:///g:/Project/data_proj_v1_trae/app/services/indicator_service.py#L641-L693)

## Excel 上传兼容
- 为 Excel 上传新增对类型字段的支持：
  - 支持列：type_id 或 type_name（二选一）。
  - 若未提供类型列，则从 Indicator 取默认 type_id。
  - 若提供的类型与 Indicator.type_id 不一致，报错或警告（建议报错）。
  - 写入目标：IndicatorDataV2；同上规则回填 major_id。
  - 修改处： [indicators.py:upload](file:///g:/Project/data_proj_v1_trae/app/api/endpoints/indicators.py#L176-L262)

## 查询与显示保持不变
- /metrics/query 与 /metrics/snapshot 已返回 v2 的数据结构（包含 major_id、type_id），前端无需改造展示逻辑。
- 图表组件已适配 items+total 响应结构。

## 校验与错误处理
- 前端：表单校验必填 type_id。
- 后端：
  - 验证 indicator_id 合法；district_id 合法；
  - 验证 type_id 与 Indicator.type_id 一致（若传入）；
  - 幂等：按 (circle_id, district_id, indicator_id, stat_date) 更新或插入。

## 验证用例
- 手动上传：选择“指标、区县、考核类型、日期、数值”上传成功，/metrics/query 能查询到新增数据且 type_id 正确。
- Excel 上传：带 type_id 或 type_name 列，上传后按类型筛选能准确显示。
- 旧数据：不带类型字段也能上传，后端自动从 Indicator 回填。

## 交付
- 代码改造最小化，不影响现有分页与查询；确保新上传的数据在 v2 中分类准确。