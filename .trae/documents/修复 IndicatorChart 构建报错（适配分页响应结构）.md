## 问题概述
- 构建时报错 TS2339：`IndicatorDataResponse` 上不存在 `map`，说明组件将响应当作数组使用。
- 目前 API 统一返回 `{ items, total }`，而 `IndicatorChart.vue` 仍按数组处理（`res.map(...)`）。

## 目标
- 适配图表组件到新的响应结构，保证趋势渲染与生产构建通过。

## 具体改动
### 1. 组件适配响应结构
- 在 `src/components/IndicatorChart.vue`：
  - 将 `const dates = res.map(...)` 替换为 `const dates = res.items.map(...)`；数值同理取 `res.items`。
  - 为保险起见，新增一个轻量归一化函数：
    - 若响应是数组，直接返回数组；若是对象，返回 `items`；避免未来接口差异导致组件崩溃。
  - 为 `res` 添加明确类型（`IndicatorDataResponse` 或 `IndicatorData[]`）并在运行时归一化。

### 2. API 与类型使用统一
- 继续沿用现有 `IndicatorDataResponse` 类型与 `getSnapshotData()` 返回 `{ items, total }` 的结构，不修改通用 API 约定。
- 组件内统一解构 `items`，不改变其他调用方。

### 3. 构建验证
- 运行前端构建，确认不再出现 TS 报错，趋势图正常渲染。

## 回滚与兼容
- 归一化函数保证即使后端临时返回纯数组，组件也可正常工作（双向兼容）。

## 交付结果
- 构建通过，图表展示趋势数据；不影响分页与其他页面逻辑。