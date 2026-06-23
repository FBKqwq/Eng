# F4 任务进度与依赖状态（Agent 共享真相源）

> **用途**：各 Agent 开工前必读本文；任务完成后仅更新**自己负责的那一行**。
> **静态编排**：见 `README.md`、`PROMPT_DISPATCH.md`
> **任务细则**：见 `F4-xx-*.md`
> **强制基线**：`location/frontend/前端开发总体规划.md`
> **前置里程碑**：F1 完成；F2 监控明细建议已完成（图表带依赖 Shell 但不阻塞 F4-03）

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
| F4-01 | F1-03、**F1-18** = `已完成`/`已合并` |
| F4-02 | F4-01 = `已完成`/`已合并` |
| F4-03 | F4-02、F4-04 = `已完成`/`已合并` |
| F4-04 | F1-04、F2-05 = `已完成`/`已合并`（或 F1-04 已有 chartTemplates 骨架） |
| F4-05 | F4-02 = `已完成`/`已合并` |
| F4-06 | F4-02 = `已完成`/`已合并` |
| F4-07 | F4-05、F4-06 = `已完成`/`已合并` |
| F4-08 | F4-02 = `已完成`/`已合并` |
| F4-09 | F4-01 ~ F4-08 均为 `已完成`/`已合并` |

---

## 3. 任务状态表

| 任务 | 负责文件/目录 | 状态 | 负责人/Agent | 完成时间 | 分支/PR | 验收摘要 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F4-01 | `api/metrics.js` | 已完成 | elk-frontend-agent (F4-01) | 2026-06-23 | 工作区 | AC-01~AC-03：六模板→aggregateLogs、USE_MOCK=false、mock 形态对齐 schema | 仅修改 metrics.js |
| F4-02 | `composables/useMetrics.js` | 已完成 | elk-frontend-agent (F4-02) | 2026-06-23 | 工作区 | AC-01~AC-04：时间窗 debounce 联动、六模板枚举映射、loading/error/data、isMock 感知、build 通过 | 仅新建 useMetrics.js |
| F4-03 | `components/monitor/ChartBand.vue` | 已完成 | elk-frontend-agent (F4-03) | 2026-06-23 | 工作区 | AC-01~AC-04：chartTemplates 配置驱动 2~3 图、useMetrics 聚合、时间窗联动、build 通过 | 仅修改 ChartBand.vue；Shell 未传 logType，待后续补 prop |
| F4-04 | `utils/logTypeMeta.js`（chartTemplates） | 已完成 | elk-frontend-agent (F4-04) | 2026-06-23 | 工作区 | AC-01~AC-04：七类各 2~3 模板对象、§3.2 对齐、F2 列/筛选未动、ChartBand 可消费、build 通过 | 仅扩展 chartTemplates 段 |
| F4-05 | `components/dashboard/HealthOverview.vue` | 已完成 | elk-frontend-agent (F4-05) | 2026-06-23 | 工作区 | AC-01~AC-04：Gauge 健康分+五 StatCard、useMetrics 三模板并行、时间窗联动、build 通过 | 仅修改 HealthOverview.vue；环比箭头待 F7-02 |
| F4-06 | `TrafficErrorPanel`+`LatencyPanel` | 已完成 | elk-frontend-agent (F4-06) | 2026-06-23 | 工作区 | AC-01~AC-04：流量错误叠加、错误分布横条+环形、耗时三系列折线、时间窗联动 | 仅修改两 vue 文件 |
| F4-07 | `dashboard/index`+`AlertDigest`+`LatestReportCard` | 已完成 | elk-frontend-agent (F4-07) | 2026-06-23 | 工作区 | AC-01~AC-04：五区块编排、预警/报告 mock 路径+演示角标、可跳转 | 仅修改三个 vue 文件 |
| F4-08 | `funnel` 组件+view | 已完成 | elk-frontend-agent (F4-08) | 2026-06-23 | 工作区 | AC-01~AC-04：五步漏斗+转化率、流失定位+错误码横条、跳转监控带 query、build 通过 | 仅修改三 vue 文件 |
| F4-09 | `frontend/DEV.md` | 已完成 | elk-frontend-agent (F4-09) | 2026-06-23 | 工作区 | AC-01~AC-04：六模板/USE_MOCK、驾驶舱/ChartBand/漏斗数据源表、§3.1/3.2/3.7 差异、F4 开发日志 | 仅修改 DEV.md；**F4 里程碑可收口** |

---

## 4. 当前可派发任务

| 可派发任务 | 原因 |
| --- | --- |
| — | **F4 已全部完成**；下一里程碑见 `task_m5/` / `task_m6/` |

> F4-01~F4-09 均已 `已完成`；后端 M1 `/logs/aggregate` 已落地；`metrics.js` 默认 `USE_MOCK=false`。

---

## 5. 变更日志

| 时间 | 操作人/Agent | 说明 |
| --- | --- | --- |
| 2026-06-23 | 初始化 | 创建 F4 任务规划（README/STATUS/PROMPT_DISPATCH + F4-01~09） |
| 2026-06-23 | elk-frontend-agent (F4-01) | metrics.js：六模板→aggregateLogs、USE_MOCK=false、契约化 mock |
| 2026-06-23 | elk-frontend-agent (F4-05) | HealthOverview：Gauge + 五 StatCard，环比箭头隐藏 |
| 2026-06-23 | elk-frontend-agent (F4-02) | useMetrics：六模板查询、useTimeRange 联动、isMock 角标支持 |
| 2026-06-23 | elk-frontend-agent (F4-03) | ChartBand：chartTemplates 驱动 Trend/Bar/Pie、useMetrics 并行、错误重试与演示角标 |
| 2026-06-23 | elk-frontend-agent (F4-04) | logTypeMeta：七类 chartTemplates 结构化配置，对齐 §3.2 图表带表 |
| 2026-06-23 | elk-frontend-agent (F4-06) | TrafficErrorPanel + LatencyPanel：流量/错误/耗时三面板 |
| 2026-06-23 | elk-frontend-agent (F4-07) | dashboard 五区块装配；AlertDigest / LatestReportCard mock 路径 |
| 2026-06-23 | elk-frontend-agent (F4-08) | funnel 主漏斗 + LossLocator 流失定位 |
| 2026-06-23 | elk-frontend-agent (F4-09) | DEV.md §6.7~6.11 F4 收敛；STATUS 更新；**F4 里程碑可收口** |
