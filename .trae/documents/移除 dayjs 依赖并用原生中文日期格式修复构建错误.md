## 问题
- 构建报错：未安装 dayjs 导致 main.ts 引入失败。

## 解决方案
- 不引入第三方库，改用原生 Date/Intl 中文格式。

## 改动点
- 前端入口：移除 main.ts 对 dayjs 的引入和 locale 设置，仅保留 Element Plus 中文本地化。
- 趋势组件：IndicatorChart.vue 的坐标轴标签使用原生 Date 格式化为“MM月DD日”。
- 列表日期：Dashboard.vue 的日期列以“YYYY年MM月DD日”显示（中文格式）。

## 验证
- 重新构建无 dayjs 依赖错误；页面日期均为中文显示；趋势图坐标轴中文标注。