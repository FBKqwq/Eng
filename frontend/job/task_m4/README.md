# F4 图表线 — 前端 Agent 任务编排说明

> 对应总体规划：`location/frontend/前端开发总体规划.md` §3.1、§3.2、§3.7、§7（阶段 F4）
> 目标：六类聚合模板驱动驾驶舱、监控图表带、漏斗页；底层 **`POST /logs/aggregate`**（非 `/metrics/*`）。
> 原则：**一个 Agent 只负责一组互不重叠的文件**。
> 边界：仅 `location/frontend/`；报告/预警真实数据留 F6，本阶段驾驶舱预警/报告卡可 mock 或半真实。

---

## 1. 阶段定位

F4 交付「图表与聚合全链路」：

- `metrics.js` 六模板 wrapper + `USE_MOCK=false` 就绪切换。
- `useMetrics` 统一时间窗联动与 loading/error。
- 驾驶舱：健康仪表、流量/错误/耗时面板。
- 监控 7 子页：`ChartBand` 接真实聚合（经 `logTypeMeta.chartTemplates`）。
- 漏斗页：`behavior_funnel` 聚合 + 流失定位。

F4 **不做**：诊断/报告/预警业务页（F5/F6）、系统页（F3）。

---

## 2. 任务清单与文件归属

| 任务编号 | 文档 | 唯一负责文件/目录 | 禁止修改 |
| --- | --- | --- | --- |
| F4-01 | [F4-01-metrics_api.md](./F4-01-metrics_api.md) | `src/api/metrics.js` | 其他所有文件 |
| F4-02 | [F4-02-use_metrics.md](./F4-02-use_metrics.md) | `src/composables/useMetrics.js`（新建） | 其他所有文件 |
| F4-03 | [F4-03-chart_band.md](./F4-03-chart_band.md) | `src/components/monitor/ChartBand.vue` | 其他所有文件 |
| F4-04 | [F4-04-log_type_charts.md](./F4-04-log_type_charts.md) | `src/utils/logTypeMeta.js`（仅 chartTemplates 段） | 其他所有文件 |
| F4-05 | [F4-05-health_overview.md](./F4-05-health_overview.md) | `src/components/dashboard/HealthOverview.vue` | 其他所有文件 |
| F4-06 | [F4-06-traffic_latency_panels.md](./F4-06-traffic_latency_panels.md) | `TrafficErrorPanel.vue` + `LatencyPanel.vue` | 其他所有文件 |
| F4-07 | [F4-07-dashboard_assembly.md](./F4-07-dashboard_assembly.md) | `views/dashboard/index.vue` + `AlertDigest.vue` + `LatestReportCard.vue` | 其他所有文件 |
| F4-08 | [F4-08-funnel_page.md](./F4-08-funnel_page.md) | `FunnelMain.vue` + `LossLocator.vue` + `views/analysis/funnel.vue` | 其他所有文件 |
| F4-09 | [F4-09-dev_docs.md](./F4-09-dev_docs.md) | `frontend/DEV.md` | 业务代码文件 |

---

## 3. 推荐执行顺序

```text
阶段 A
  F4-01 metrics.js              ← 六模板 + USE_MOCK 开关

阶段 B
  F4-02 useMetrics.js           ← 依赖 F4-01

阶段 C（可并行）
  F4-04 logTypeMeta chartTemplates
  F4-05 HealthOverview.vue
  F4-06 TrafficErrorPanel + LatencyPanel

阶段 D
  F4-03 ChartBand.vue           ← 依赖 F4-02、F4-04

阶段 E
  F4-07 dashboard 装配          ← 依赖 F4-05/06；AlertDigest/ReportCard mock 分界

阶段 F
  F4-08 funnel 页               ← 依赖 F4-02

阶段 G
  F4-09 dev_docs
```

---

## 4. 跨任务约定

1. 聚合口径**仅**使用后端六模板（traffic / errors / latency / behavior_funnel / security / infra_health），前端不自创聚合。
2. 时间窗统一 `useTimeRange()` inject；变更触发 `useMetrics` 重查。
3. `USE_MOCK=true` 时页内必须显示「演示数据」角标；后端 M1 就绪后 F4-01 改 `USE_MOCK=false`。
4. ECharts 仅存在于 `components/common/charts/`；业务组件只传 data/option。
5. F4-04 与 F2-05 共享 `logTypeMeta.js`——F4-04 **只扩展** `chartTemplates`，不改 defaultColumns/fallbackFilters。
6. 全部简体中文；除非负责人明确要求，**不要 commit**。

---

## 5. F4 总体验收

- [ ] 驾驶舱健康仪表 + 三趋势图随全局时间窗刷新。
- [ ] 7 个监控子页图表带展示对应模板图表（或接口离线时 EmptyState + 错误态）。
- [ ] 漏斗页五步漏斗 + 流失定位可用。
- [ ] `metrics.js` 六模板函数齐全；`USE_MOCK` 可切换。
- [ ] `npm run build` 通过；DEV.md 更新。

---

## 6. 后端依赖

| 接口 | 状态 | F4 行为 |
| --- | --- | --- |
| `POST /api/v1/logs/aggregate` | M1 已落地 | `metrics.js` 六模板封装 → `aggregateLogs` |
| `GET /api/v1/alerts/active` | M5 已落地 | F4-07 AlertDigest 可接真实或 mock |
| `GET /api/v1/reports/recent` | M4 已落地 | F4-07 LatestReportCard 可接真实或 mock |
