# F6 任务进度与依赖状态（Agent 共享真相源）

> **用途**：各 Agent 开工前必读本文；任务完成后仅更新**自己负责的那一行**。
> **静态编排**：见 `README.md`、`PROMPT_DISPATCH.md`
> **任务细则**：见 `F6-xx-*.md`
> **强制基线**：`location/frontend/前端开发总体规划.md`
> **前置里程碑**：F1 完成；F4-07 驾驶舱摘要占位建议已完成

---

## 1. 状态枚举

| 状态 | 含义 |
| --- | --- |
| `未开始` | 尚未派发或无人认领 |
| `进行中` | Agent 已开工，代码未验收 |
| `已完成` | 本任务 AC/DoD 已通过 |
| `已合并` | 已合入团队约定的集成分支 |
| `阻塞` | 因依赖或环境问题无法继续 |

**下游依赖以 `已合并` 为准**；单分支开发时 `已完成` 可视同 `已合并`。

---

## 2. 派发前依赖检查

| 任务 | 可派发条件 |
| --- | --- |
| F6-01 | F1-18 = `已完成`/`已合并` |
| F6-02 | F1-18 = `已完成`/`已合并` |
| F6-03 | F6-01 = `已完成`/`已合并` |
| F6-04 | F6-03 = `已完成`/`已合并` |
| F6-05 | F6-02 = `已完成`/`已合并` |
| F6-06 | F6-05 = `已完成`/`已合并` |
| F6-07 | F6-01、F6-02、F4-07 = `已完成`/`已合并` |
| F6-08 | F6-01 ~ F6-07 均为 `已完成`/`已合并` |

---

## 3. 任务状态表

| 任务 | 负责文件/目录 | 状态 | 负责人/Agent | 完成时间 | 分支/PR | 验收摘要 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F6-01 | `api/reports.js` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-05：getRecentReports/getReportDetail 对齐信封 data、mock items+total+limit / report:null、默认 USE_MOCK=false | —
| F6-02 | `api/alerts.js` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04：getActiveAlerts/acknowledgeAlert 对齐信封 data、mock items+total、默认 USE_MOCK=false | —
| F6-03 | reports 三组件 | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04：时间轴可选中、风险仪表+理由、三节要点、node_trace 页脚阶段环 | F6-04 可装配 |
| F6-04 | `views/analysis/reports.vue` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04：时间轴+默认选中最新、右栏详情联动、空态、build OK | RelationInsightCard 占位保留 |
| F6-05 | alerts 三组件 | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04：三态计数+24h趋势、表格列+确认emit、抽屉三段解释+诊断emit、build OK | F6-06 可装配 |
| F6-06 | `views/analysis/alerts.vue` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04：getActiveAlerts 驱动看板+表、ack 后刷新、抽屉详情、诊断 query alert_id、30s 轮询 | —
| F6-07 | TopBar+AlertDigest+LatestReportCard | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04：TopBar 30s 轮询真实角标、两摘要卡真实 API、跳转正确、无演示角标 | ack 后下次轮询更新角标 |
| F6-08 | `frontend/DEV.md` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04：reports/alerts API 与 USE_MOCK 文档化、两页+全局接线 §6.16~6.18、F6 开发日志 | F6 里程碑文档收敛 |

---

## 4. 当前可派发任务

| 可派发任务 | 原因 |
| --- | --- |
| — | F6 全部任务已完成；下一阶段见 `task_m7/` |

> F6-01/02 不可在 mock 形态未修正前仅关 `USE_MOCK`。

---

## 5. 变更日志

| 时间 | 操作人/Agent | 说明 |
| --- | --- | --- |
| 2026-06-23 | 初始化 | 创建 F6 任务规划（README/STATUS/PROMPT_DISPATCH + F6-01~08） |
| 2026-06-23 | elk-frontend-agent | F6-01 完成：reports.js USE_MOCK=false，列表/详情契约注释与 mock 形态 |
| 2026-06-23 | elk-frontend-agent | F6-02 完成：alerts.js USE_MOCK=false，活跃列表/确认契约注释与 mock items+total |
| 2026-06-23 | elk-frontend-agent | F6-03 完成：ReportTimeline/ReportRiskPanel/ReportSections props 驱动，阶段环+统计模式角标 |
| 2026-06-23 | elk-frontend-agent | F6-05 完成：AlertBoard/AlertTable/AlertDetailDrawer 三组件 props+emit 契约 |
| 2026-06-23 | elk-frontend-agent | F6-04 完成：reports.vue 装配时间轴/风险/拆解，mount 拉列表默认选最新、详情联动 |
| 2026-06-23 | elk-frontend-agent | F6-06 完成：alerts.vue 装配 API+三组件、ack 刷新、诊断跳转、30s 静默轮询 |
| 2026-06-23 | elk-frontend-agent | F6-07 完成：TopBar 30s 轮询角标、AlertDigest/LatestReportCard 接真实 API、移除演示数据 |
| 2026-06-23 | elk-frontend-agent | F6-08 完成：DEV.md §6.16~6.18 收敛 F6 结果线（API/页面/全局接线）、§8 F6 验收、§12 日志 |
