# F1-05：ECharts 图表薄封装 charts

## Agent 角色

图表基础件专项 Agent — **仅实现 ECharts 薄封装（只收 option/data，不含业务）**。

## 唯一负责文件

```
src/components/common/charts/BaseChart.vue
src/components/common/charts/GaugeChart.vue
src/components/common/charts/TrendChart.vue
src/components/common/charts/BarChart.vue
src/components/common/charts/PieChart.vue
src/components/common/charts/FunnelChart.vue
```

## 禁止修改

- `components/common/` 下非 charts 的组件（归 F1-06）
- `views/`、`layout/`、`api/` 等任何其他文件

## 前置依赖

- F1-01 设计令牌（配色/尺寸复用）
- 依赖项 `echarts`（已在 `package.json`）

## 开发要求

### 1. `BaseChart.vue`（核心）

- **唯一** `import echarts` 之处（按需注册可选）。
- props：`option`（Object）、`loading`（Boolean）、`height`（String）、`emptyText`（String）。
- 能力：初始化实例、`option` 变化时更新、窗口 `resize` 自适应、`loading` 态、无数据时显示 `emptyText` 空态。
- 组件卸载时 `dispose` 实例。

### 2. 5 个业务无关图表

`GaugeChart` / `TrendChart` / `BarChart` / `PieChart` / `FunnelChart`：

- 均基于 `BaseChart`，对外只暴露 data/配置与 `placeholder`，内部组装对应 `option`。
- 无数据时显示占位文案（如「仪表盘占位：等待聚合接口」），不报错。

### 3. 约束（强制）

- **图表只进不出**：ECharts 实例只允许存在于本目录；页面组件传 data/option，不直接 `import echarts`。
- 不在图表内发请求、不写业务聚合口径。
- 简体中文注释与占位文案。

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | BaseChart | 接收 option 渲染，resize 自适应，卸载 dispose |
| AC-02 | 空态 | 无数据时显示 `emptyText`/`placeholder`，不报错 |
| AC-03 | 6 组件 | BaseChart + 5 图表均可独立挂载 |
| AC-04 | 隔离 | 仅 `BaseChart.vue` import echarts |
| AC-05 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 charts/ 下 6 个文件
- [ ] 仅 BaseChart import echarts
- [ ] 不修改 DEV.md

## 下游消费说明（供其他 Agent 只读）

- F1-12 dashboard、F1-13 monitor、F1-14 analysis 的占位区块复用这些图表
- `GaugeChart` 供健康分/严重度/置信度/风险级复用
