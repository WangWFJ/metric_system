## 目标
- 将数据源切换为新表 indicator_data_v2（含 type_id、major_id）。
- 修复并简化按区县、专业、考核类型的筛选和分页，保证完整性与准确性。
- 保持接口返回结构不变（items+total），前端无感知改造或最小改动。

## 数据模型更新
- 在 models 中新增 ORM 模型 IndicatorDataV2 映射到表 indicator_data_v2，字段覆盖：indicator_id、indicator_name、type_id、major_id、is_positive、circle_id、district_id、district_name、stat_date、value、benchmark、challenge、exemption、zero_tolerance、score、create_time、update_time。
- 若原有 IndicatorData 模型仍存在，逐步替换所有查询/写入到 IndicatorDataV2。
- 文件：
  - [metrics.py](file:///g:/Project/data_proj_v1_trae/app/models/metrics.py)

## 服务层改造
- 统一改造以下函数，数据源改为 IndicatorDataV2：
  - query_metrics：改为直接使用 IndicatorDataV2 做筛选；major_id/type_id 直接在数据表上过滤；必要时 JOIN Indicator 附加 status==1 过滤（避免停用指标数据混入）。
    - 替换位置：[indicator_service.py:query_metrics](file:///g:/Project/data_proj_v1_trae/app/services/indicator_service.py#L140-L192)
  - latest_metrics：在上述过滤基础上，用窗口函数按 (indicator_id, district_id) 取各自最新一条；直接从 IndicatorDataV2 读取 major_id/type_id。
    - 替换位置：[indicator_service.py:latest_metrics](file:///g:/Project/data_proj_v1_trae/app/services/indicator_service.py#L194-L268)
  - get_indicators_by_district：默认返回该区县“最新快照”（每个指标最新值），不再依赖“全局同一天”；提供可选日期参数返回某日数据。
    - 位置：[indicator_service.py:get_indicators_by_district](file:///g:/Project/data_proj_v1_trae/app/services/indicator_service.py#L203-L278)
  - get_latest_indicator_data：改用 IndicatorDataV2；当传 indicator_name 时先查 Indicator.indicator_id。
    - 位置：[indicator_service.py:get_latest_indicator_data](file:///g:/Project/data_proj_v1_trae/app/services/indicator_service.py#L282-L331)
  - get_metrics_by_major / get_metrics_by_type：保留聚合结构，但数据源改为 IndicatorDataV2，优先用数据表中的 major_id/type_id；若需过滤停用指标，JOIN Indicator 加 status==1。
    - 位置：[indicator_service.py:get_metrics_by_major](file:///g:/Project/data_proj_v1_trae/app/services/indicator_service.py#L332-L498)、[indicator_service.py:get_metrics_by_type](file:///g:/Project/data_proj_v1_trae/app/services/indicator_service.py#L498-L661)
- 计数与分页：全部使用子查询计数（select(func.count()).select_from(subquery)），保证 total 准确。

## 写入与上传改造
- create_indicator_data：写入 IndicatorDataV2；在写入前查询 Indicator 获取其 major_id、type_id 并回填至 v2（保持反规范化一致性）；实现基于 (circle_id, district_id, indicator_id, stat_date) 的幂等 upsert（先查则更新，不存在则插入）。
  - 位置：[indicator_service.py:create_indicator_data](file:///g:/Project/data_proj_v1_trae/app/services/indicator_service.py#L700-L752)
- /upload：Excel 上传改为生成 IndicatorDataV2 行，并同样填充 major_id、type_id；遇到重复行执行更新。
  - 位置：[indicators.py:upload](file:///g:/Project/data_proj_v1_trae/app/api/endpoints/indicators.py#L144-L231)

## API 层与返回结构
- /metrics/query 与 /metrics/snapshot 保持不变，仅内部数据源切换到 IndicatorDataV2。
  - 位置：[indicators.py](file:///g:/Project/data_proj_v1_trae/app/api/endpoints/indicators.py#L110-L176)、[indicators.py](file:///g:/Project/data_proj_v1_trae/app/api/endpoints/indicators.py#L178-L244)
- 如仍保留老接口路径，确保返回结构 { items, total } 不变。

## Schema 更新
- 在 metrics_schemas 中将 IndicatorDataOut 增加 major_id、type_id 字段（与 v2 同步）；其它结构保持。
  - 位置：[metrics_schemas.py](file:///g:/Project/data_proj_v1_trae/app/models/metrics_schemas.py)

## 前端适配
- 类型定义：IndicatorData 增加 major_id、type_id 字段；其余无需改动。
  - 位置：[frontend/src/api/indicator.ts](file:///g:/Project/data_proj_v1_trae/frontend/src/api/indicator.ts)
- 组件：若展示分类信息，可直接读取返回项的 major_id/type_id；分页逻辑保持使用 items+total。

## 验证与回归
- 后端：
  - 未筛选 /metrics/query?page=1&size=20 → total≈全库记录数，items=20；翻页正常。
  - 区县快照 /metrics/snapshot?district_id=xxx → 每个指标均返回该区县最新值。
  - 专业/类型筛选 → 直接依据 v2 中的 major_id/type_id，分类准确；若 JOIN Indicator.status==1 启用，则停用指标数据不返回。
- 前端：
  - 仪表板列表与趋势图（IndicatorChart）正常展示与构建通过。

## 迁移注意
- 若保留旧表 indicator_data，仅用于历史参考；全量查询/写入切换到 v2。
- 若需数据迁移脚本，可按 indicator_id/district_id/stat_date 对齐并补齐 major_id/type_id。