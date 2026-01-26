## 目标
- 在仪表板中新增“导出为Excel”按钮，导出当前筛选条件下的指标数据。
- 所有角色均可使用（满足 indicator_data:view 即可，viewer 已具备）。

## 后端接口
- 新增 GET /api/v1/metrics/export（依赖 indicator_data:view）
- 参数：与仪表板查询一致（indicator_id、district_id/district_name、start_date、end_date、major_id、type_id、order_by、desc、size等）。
- 实现：复用 query_metrics/latest_metrics/series 的数据获取逻辑，组织为 DataFrame，返回 .xlsx 文件（StreamingResponse，Content-Disposition 设置文件名，如 metrics_export_YYYYMMDD.xlsx）。
- 列：indicator_name、district_name、stat_date、value、score、benchmark、challenge、exemption、zero_tolerance（存在则导出）。

## 前端实现
- 在 Dashboard.vue 的筛选/操作区域新增“导出Excel”按钮。
- 新增前端 API：exportMetrics(params) → GET /metrics/export，responseType: 'blob'。
- 下载处理：从响应头解析文件名，使用 URL.createObjectURL 触发浏览器下载。
- 参数来源：沿用页面当前的筛选条件（与查询接口同源）。

## 权限与体验
- 路由保持 requiresAuth；接口依赖 indicator_data:view，viewer/data_entry/indicator_admin/admin均可导出。
- 加载状态与错误提示：按钮 loading，失败弹出错误信息。

## 验证
- 各角色导出对应数据，无403。
- 大数据量分页处理：导出接口内部自动拉取完整数据（或限定最大行数为10万），避免只导出当前页。

## 交付
- 后端导出接口、前端按钮与下载逻辑，统一列结构与文件名；不改动现有查询逻辑。