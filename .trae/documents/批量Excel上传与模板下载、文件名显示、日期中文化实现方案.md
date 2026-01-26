## 功能概述

* 批量上传：支持选择Excel文件，批量导入具体指标数据（含得分、豁免值、零容忍值等）。

* 模板下载：提供Excel模板下载入口与页面提示，指导用户按模板填充。

* 选择文件名显示：文件选择后在前端展示当前已选择的文件名。

* 日期中文化：前端所有日期显示统一为中文样式（如“2026年01月13日”）。

## 后端改造

### 批量上传接口（沿用，强化校验）

* 现有接口：POST /api/v1/metrics/upload（已实现解析列 indicator\_name、district\_name、stat\_date、value、benchmark、challenge、exemption、zero\_tolerance、score）[indicators.py](file:///g:/Project/data_proj_v1_trae/app/api/endpoints/indicators.py#L176-L294)

* 调整/增强：

  * 允许日期列支持多种格式（YYYY-MM-DD、YYYY/MM/DD、YYYY年MM月DD日），统一解析为 date。

  * 批量错误汇总时返回前10条错误，页面提示。

  * 返回成功导入条数与跳过/更新条数统计（可选）。

### 模板下载接口（新增）

* 新增：GET /api/v1/metrics/upload/template

* 返回：一个Excel文件（Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet），包含表头与示例行：

  * 必填：indicator\_name、district\_name、stat\_date、value

  * 选填：benchmark、challenge、exemption、zero\_tolerance、score、

  * type\_id和major\_id等自动根据数据库中指标库自行匹配

  * 且每一个英文列都需有中文注释

* 实现方式：

  * 简便：后端生成DataFrame写入BytesIO并返回（pandas+openpyxl），或读取项目内静态模板文件并流式返回（assets/templates/indicator\_import\_template.xlsx）。

## 前端改造

### API

* 已有上传API：uploadIndicatorData(file) [indicator.ts](file:///g:/Project/data_proj_v1_trae/frontend/src/api/indicator.ts#L96-L104)

* 新增模板下载API：getUploadTemplate()，请求 /metrics/upload/template，获取blob并触发下载。

### 页面（Dashboard）

* 上传区域（上传对话框底部或单独卡片）：

  * 增加“下载模板”按钮，调用 getUploadTemplate 并保存为 indicator\_import\_template.xlsx。

  * 使用 el-upload（limit=1、auto-upload=false）或自定义 input\[type=file]：

    * 选择文件后，显示当前文件名；

    * 点击“上传”时调用 uploadIndicatorData(file)，loading状态与成功/失败提示；

    * 成功后刷新列表。

* 指标上传表单保留（手动单条），批量上传与单条上传并行可用。[Dashboard.vue](file:///g:/Project/data_proj_v1_trae/frontend/src/views/Dashboard.vue)

### 日期中文化

* 全局：

  * 在 main.ts 设置 Element Plus 中文：import zhCn from 'element-plus/dist/locale/zh-cn.mjs'；app.use(ElementPlus, { locale: zhCn })；

  * 设置 dayjs 中文：import 'dayjs/locale/zh-cn'；dayjs.locale('zh-cn')；

* 组件显示：

  * el-date-picker 仍用 value-format='YYYY-MM-DD' 保持后端一致；显示在表格中使用 dayjs(stat\_date).format('YYYY年MM月DD日')。[Dashboard.vue](file:///g:/Project/data_proj_v1_trae/frontend/src/views/Dashboard.vue)

  * 趋势图x轴使用 time 类型，axisLabel formatter 结合 dayjs 中文本地化显示，例如 'MM月DD日' 或 'YYYY年MM月'。[IndicatorChart.vue](file:///g:/Project/data_proj_v1_trae/frontend/src/components/IndicatorChart.vue)

## 交互与校验

* 文件类型校验：限制 .xls/.xlsx；非模板列名或缺失必填列时，前端提示并拒绝导入。

* 进度与反馈：上传中禁用按钮，完成后通知“成功导入N条，更新M条（可选）”。

* 错误显示：后端返回的前10条错误在通知中显示（简短）。

## 验证

* 下载模板→填充若干行（含不同日期格式与得分/豁免/零容忍）→选择文件→显示文件名→上传→列表刷新并显示中文日期与得分列。

* 趋势图中文日期显示正确；单条上传仍正常。

## 兼容性与安全

* 上传体积限制（例如<10MB），后端按需配置。

* 所有入参与数据统一为UTC或本地日期，无时区偏移问题（仅日期）。

* 不改变现有API响应结构（items+total）。

