## 问题诊断
- 区县查询仅显示少量数据：当前实现按区县取“全局最新一天”的数据（如 [get_indicators_by_district](file:///g:/Project/data_proj_v1_trae/app/services/indicator_service.py#L203-L278)），导致该日无数据的指标全部缺失。
- 专业/考核类型分类混乱：分类应以 indicator 表中的 `major_id`、`type_id` 为准，但可能混入停用或旧版（status≠1，version 较旧）的指标，使同一编码出现在不同分类。
- 统计与分页：未筛选时总数统计不稳（历史实现使用 with_only_columns），前端分页不可用。

## 改造目标
- 区县查询：支持两种模式
  - 最新快照（每个“指标×区县”取自身最新一条，不受“全局最新日”影响）
  - 时间序列（按区县+日期范围分页列出所有记录）
- 分类筛选：严格按 indicator.major_id 与 indicator.type_id；默认仅取 Indicator.status=1；必要时按 indicator_code 选择最新版本去重。
- 分页统计：统一使用“子查询计数”的稳健方案，确保 total 正确。

## 接口设计
- GET /api/v1/metrics/query
  - 作用：通用分页查询原始数据（IndicatorData）
  - 筛选：district_id/district_name、major_id、type_id、indicator_id/indicator_code、start_date/end_date、circle_id
  - 返回：{ items: IndicatorDataOut[], total }
- GET /api/v1/metrics/snapshot
  - 作用：每个“指标×区县”的最新值（看板使用）
  - 同样支持区县/专业/类型筛选，不依赖“全局同一天”
  - 返回：{ items, total }
- 可选新增（按需）：
  - GET /api/v1/metrics/district/latest（强制要求 district，并按该区县做快照）
  - GET /api/v1/metrics/district/query（区县时间序列，必须带日期范围）

## 服务层实现
- query_metrics（文件： [indicator_service.py](file:///g:/Project/data_proj_v1_trae/app/services/indicator_service.py)）
  - 始终 JOIN Indicator；统一添加 `Indicator.status == 1`
  - 分类过滤：`Indicator.major_id == :major_id`、`Indicator.type_id == :type_id`
  - 日期：`IndicatorData.stat_date BETWEEN :start/:end`
  - 统计：`select(func.count()).select_from(stmt.subquery())`
  - 排序+分页：在统计之后应用
- latest_metrics（文件： [indicator_service.py](file:///g:/Project/data_proj_v1_trae/app/services/indicator_service.py)）
  - 在上述过滤基础上，窗口函数：`row_number() over(partition by IndicatorData.indicator_id, IndicatorData.district_id order by stat_date desc)` 取 rn=1
  - 统计与分页同上
- 若存在“同一编码多版本”且分类发生变化：在按分类筛选前，用窗口函数按 `indicator_code` 选择最新且 `status=1` 的版本，避免旧版混入导致分类混乱。

## 前端适配
- 仪表板“最新指标”使用 /metrics/snapshot；列表查询使用 /metrics/query
- 统一响应结构 `{ items, total }`；已在图表组件适配 `items`（见 [IndicatorChart.vue](file:///g:/Project/data_proj_v1_trae/frontend/src/components/IndicatorChart.vue)）
- 保留分页控件逻辑不变

## 验证用例
- 未筛选：/metrics/query?page=1&size=20 → total≈全库记录数（两千+），items=20；翻页正常
- 区县快照：/metrics/snapshot?district_id=xxx → 每个指标均返回该区县的最新值
- 区县时间序列：/metrics/query?district_id=xxx&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD → 分页与总数正确
- 分类准确性：传 major_id 或 type_id → 只返回该分类指标（status=1），无跨分类重复

## 备注
- 若需支持按名称筛选（major_name、type_name），可在 query_metrics/最新快照中按需 JOIN majors/evaluation_types 并使用 LIKE 过滤。
- 后续如需“以编码维度进行版本去重”，在服务层统一追加按 `indicator_code` 的窗口函数去重步骤。