# F1-12：总览驾驶舱占位 dashboard_placeholder

## Agent 角色

驾驶舱页面占位专项 Agent — **仅搭建驾驶舱页面骨架与占位区块**（不接真实数据）。

## 唯一负责文件/目录

```
src/views/dashboard/index.vue
src/components/dashboard/HealthOverview.vue
src/components/dashboard/TrafficErrorPanel.vue
src/components/dashboard/LatencyPanel.vue
src/components/dashboard/AlertDigest.vue
src/components/dashboard/LatestReportCard.vue
```

## 禁止修改

- `components/common/`、`components/monitor|analysis-*|system/`、其他页面 views
- `router/index.js`、`layout/`

## 前置依赖

- F1-05 charts、F1-06 common（`EmptyState`/`StatCard`/`GaugeChart` 等）

## 开发要求

### 1. 页面编排 `views/dashboard/index.vue`

按总体规划 §3.1 分区组合各子组件（健康总仪表 + 指标带 / 流量错误 / 耗时 / 预警摘要 / 最新体检结论）。

### 2. 子组件（F1 全部为占位）

| 组件 | 占位形式 |
| --- | --- |
| `HealthOverview` | `EmptyState`，`pending-api="metrics 聚合接口"`（含健康分仪表 + 5 指标卡占位） |
| `TrafficErrorPanel` | 空 `TrendChart` 占位 |
| `LatencyPanel` | 空 `TrendChart` 占位 |
| `AlertDigest` | `EmptyState`，`pending-api="GET /api/v1/alerts/active"`，compact |
| `LatestReportCard` | `EmptyState`，`pending-api="GET /api/v1/reports/recent"`，compact |

### 3. 约束

- 仅 view 组合 + 组件占位，不接真实渲染（留待 F4/F6）。
- 不直接 `import echarts`；图表用 F1-05 组件。
- 简体中文文案。

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 页面可达 | `/dashboard` 渲染不报错 |
| AC-02 | 分区 | 5 个区块按 §3.1 编排 |
| AC-03 | 占位标注 | 待接入区块用 `EmptyState` + `pending-api` |

## 完成定义（DoD）

- [ ] 仅修改 dashboard 视图与组件
- [ ] 不修改 DEV.md

## 下游消费说明（供其他 Agent 只读）

- F1-16 router 注册 `/dashboard`
- F4/F6 将替换占位为真实数据
