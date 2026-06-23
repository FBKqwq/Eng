# F6 结果线 — 前端 Agent 任务编排说明

> 对应总体规划：`location/frontend/前端开发总体规划.md` §3.4、§3.5、§7（阶段 F6）
> 目标：周期体检报告 + 预警中心 + 全局预警角标 + 驾驶舱真实数据切换。
> 原则：**一个 Agent 只负责一组互不重叠的文件**。

---

## 1. 阶段定位

F6 交付「智能体结果可见可操作」：

- 报告页：时间轴 + 风险定级 + 结构化拆解。
- 预警页：三态看板 + 列表 + ack + 详情抽屉。
- 全局：`TopBar` 角标、`AlertDigest`、`LatestReportCard` 接真实 API（`USE_MOCK=false`）。

F6 **不做**：诊断/trace（F5）、聚合图表（F4 已完成）。

---

## 2. 任务清单与文件归属

| 任务编号 | 文档 | 唯一负责文件/目录 | 禁止修改 |
| --- | --- | --- | --- |
| F6-01 | [F6-01-reports_api.md](./F6-01-reports_api.md) | `src/api/reports.js` | 其他所有文件 |
| F6-02 | [F6-02-alerts_api.md](./F6-02-alerts_api.md) | `src/api/alerts.js` | 其他所有文件 |
| F6-03 | [F6-03-reports_components.md](./F6-03-reports_components.md) | `ReportTimeline` + `ReportRiskPanel` + `ReportSections` | 其他所有文件 |
| F6-04 | [F6-04-reports_view.md](./F6-04-reports_view.md) | `views/analysis/reports.vue` | 其他所有文件 |
| F6-05 | [F6-05-alerts_components.md](./F6-05-alerts_components.md) | `AlertBoard` + `AlertTable` + `AlertDetailDrawer` | 其他所有文件 |
| F6-06 | [F6-06-alerts_view.md](./F6-06-alerts_view.md) | `views/analysis/alerts.vue` | 其他所有文件 |
| F6-07 | [F6-07-global_alert_wiring.md](./F6-07-global_alert_wiring.md) | `TopBar.vue` + `AlertDigest.vue` + `LatestReportCard.vue` | 其他所有文件 |
| F6-08 | [F6-08-dev_docs.md](./F6-08-dev_docs.md) | `frontend/DEV.md` | 业务代码文件 |

---

## 3. 推荐执行顺序

```text
阶段 A（可并行）
  F6-01 reports.js
  F6-02 alerts.js

阶段 B（可并行）
  F6-03 reports 三组件
  F6-05 alerts 三组件

阶段 C（可并行）
  F6-04 reports.vue
  F6-06 alerts.vue

阶段 D
  F6-07 全局接线（依赖 F6-01/02 与 F4-07 已有组件）

阶段 E
  F6-08 dev_docs
```

---

## 4. 跨任务约定

1. **F1-18 完成后** reports/alerts 默认 `USE_MOCK=false`（M4/M5 已落地）；离线调试可临时 true 并显示「演示数据」角标。
2. 解包后读 `res.data.items` / `res.data.total`；错误 `catch (e.error?.code)`。
3. 预警解释文案三段式：现象 / 影响 / 建议（§3.5），禁止对话流。
4. `POST /alerts/{id}/ack` 成功后刷新列表与 TopBar 角标。
5. 详情抽屉「深度诊断」→ `/analysis/diagnosis?alert_id=`。
6. RelationInsightCard 真实数据属 F7-01，F6-03 不包含。
7. 全部简体中文；不要 commit。

---

## 5. F6 总体验收

- [ ] 报告页可选中历史报告并拆解展示；node_trace 页脚阶段点可见。
- [ ] 预警页三态计数、列表、ack、抽屉完整。
- [ ] TopBar 角标 30s 轮询真实 active 数；驾驶舱摘要卡真实数据。
- [ ] `npm run build` 通过；DEV.md 更新。

---

## 6. 后端依赖

| 接口 | 状态 | F6 行为 |
| --- | --- | --- |
| `GET /api/v1/reports/recent`、`GET /api/v1/reports/{id}` | M4 已落地 | `USE_MOCK=false`；`data.items`+`report` |
| `GET /api/v1/alerts/active`、`POST /api/v1/alerts/{id}/ack` | M5 已落地 | `USE_MOCK=false`；角标用 `data.total` |
