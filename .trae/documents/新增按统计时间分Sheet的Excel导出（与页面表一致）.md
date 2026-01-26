**目标**

* 在现有系统中新增/完善“导出Excel（.xlsx）”功能，使导出结果与页面当前展示一致；按统计时间分Sheet；行按区县（含圈层分组），列为各指标；包含汇总行与可读性样式。

**后端实现**

* 接口：新增 /api/v1/metrics/export\_v2，参数与页面查询一致，支持 district\_ids 多选、circle\_id、type\_id、major\_id、start\_date/end\_date 等。

* 数据抓取：调用现有 query\_metrics/最新数据方法，按当前过滤条件一次性取全量结果；确保取到字段 indicator\_id、indicator\_name、stat\_date、district\_id、district\_name、circle\_id、value、is\_positive。

* 结构转换：

  * 按 stat\_date 分组生成多个 Sheet，Sheet 名称为统计时间（如 2025-01-01、2024-12）。

  * 每个 Sheet：

    * 行：区县；包含圈层列（circle\_id 或圈层名）与区县列；按圈层分组排序（第一组、第二组、第三组）。

    * 列：各指标（indicator\_name 为列头）；列顺序与页面显示顺序一致（默认按 indicator\_name 升序或按“页面最近一次查询结果的指标顺序”）。

    * 单元格值：该区县在该统计日该指标的 value；不存在用空白。

  * 汇总行：

    * “成都总计”：默认计算同一统计日下所有区县该指标的平均值（或加总，依据指标类型可扩展配置）。

    * “全市最优值”：正向指标取最大值，负向指标取最小值；依据 is\_positive 字段判断。

* 样式：

  * 表头加粗；首列圈层、区县加粗；每个圈层块之间加入细分隔样式（可用空行或浅色背景交替）。

  * 使用 pandas + openpyxl 设置加粗与自动列宽；不合并单元格（保留筛选友好）。

* 输出：

  * 返回 application/vnd.openxmlformats-officedocument.spreadsheetml.sheet，文件名 metrics\_export.xlsx。

**前端集成**

* 按钮：沿用“导出Excel”按钮；点击时携带当前所有筛选参数（含 district\_ids 多选与 circle\_id）。

* 若后端沿用旧接口：前端的导出方法 exportMetrics 增加 district\_ids 参数传递；否则切换到新路径。

**一致性要求**

* 导出数据严格依据页面当前筛选条件（指标、区县、圈层、类型、专业、日期范围）；排序与页面一致。

* 包含页面显示的汇总行（总计与最优值）。

**验证**

* 用三种场景测试：

  1. 单统计日 + 多指标 + 多区县；
  2. 多统计日范围（多Sheet）；
  3. 含圈层过滤、含 district\_ids 多选。

* 校验：Sheet 命名、行列对齐、数值与页面一致；汇总计算正确；样式满足加粗与分组。

**扩展**

* 后续可支持：单位行（在表头下方展示单位）、导出“得分/基准/挑战/豁免/零容忍”并行的可选开关、导出 CSV。

