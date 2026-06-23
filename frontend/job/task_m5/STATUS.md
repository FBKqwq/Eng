# F5 任务进度与依赖状态（Agent 共享真相源）

> **用途**：各 Agent 开工前必读本文；任务完成后仅更新**自己负责的那一行**。
> **静态编排**：见 `README.md`、`PROMPT_DISPATCH.md`
> **任务细则**：见 `F5-xx-*.md`
> **强制基线**：`location/frontend/前端开发总体规划.md` §5
> **前置里程碑**：F1 完成；F2 trace 跳转建议已完成

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
| F5-01 | F1-18 = `已完成`/`已合并` |
| F5-02 | F5-01 = `已完成`/`已合并` |
| F5-03 | F5-01 = `已完成`/`已合并` |
| F5-04 | F5-01 = `已完成`/`已合并` |
| F5-05 | F5-01、F1-06 = `已完成`/`已合并` |
| F5-06 | F5-02~05 = `已完成`/`已合并` |
| F5-07 | F1-18 = `已完成`/`已合并`（`searchByTraceId` 就位） |
| F5-08 | F5-07、F2-01 = `已完成`/`已合并` |
| F5-09 | F5-01 ~ F5-08 均为 `已完成`/`已合并` |

---

## 3. 任务状态表

| 任务 | 负责文件/目录 | 状态 | 负责人/Agent | 完成时间 | 分支/PR | 验收摘要 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F5-01 | `api/diagnosis.js` + `api/analysis.js` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-05 通过：submitDiagnosis data.diagnosis 齐全、analysis 两函数+120s 超时、文档注明无 node_trace、mock 规则降级+轨迹摘要、build OK | F5-02~05 可依赖 |
| F5-02 | `DiagnosisEntryPanel.vue` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04 通过：三入口切换、emit 规范化 payload、route query 预填、build OK | F5-06 可接入 @submit |
| F5-03 | `ConclusionPanel.vue` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04 通过：双仪表先于文字、版式化根因卡、降级角标+区间文案、空态 EmptyState | F5-06 可接入 props |
| F5-04 | `EvidenceTimeline`+`ServiceTopology` | 已完成 | F5-04 Agent | 2026-06-23 | — | AC-01~04：props 驱动时间轴/拓扑/迷你柱图，build 通过 | 待 F5-06 装配数据流 |
| F5-05 | `SuggestionChecklist`+`DiagnosisStageRing` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04 通过：建议可勾选、node_trace 映射五阶段、LLM 跳过/降级展示、未改 StageRing | F5-06 可接入 |
| F5-06 | `views/analysis/diagnosis.vue` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04 通过：四区 §3.3 布局、submitDiagnosis 提交流+面板分发、规则降级角标、mock 页级角标、build OK | F6 深度诊断跳转可消费 |
| F5-07 | `TraceSearchBar`+`TraceWaterfall` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04 通过：检索 emit+历史 localStorage、CSS 泳道瀑布+ERROR 着色+断点标记+字段展开、build OK | F5-08 可装配 trace.vue |
| F5-08 | `views/analysis/trace.vue` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04 通过：query trace_id 自动检索、手动搜索、空结果/es_unavailable 错误态+重试、build OK | F5-09 可更新 DEV.md |
| F5-09 | `frontend/DEV.md` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04 通过：§6.12 诊断四区、§6.13 trace API、§6.14 node_trace 映射、§6.15 §5 禁止项、§12 F5 日志 | F5 里程碑文档收敛完成 |

---

## 4. 当前可派发任务

| 可派发任务 | 原因 |
| --- | --- |
| — | **F5 全部完成**（F5-01~F5-09）；可启动 F6 |

> F5 与 F6 可并行（不同目录）；F5 文档基线见 `frontend/DEV.md` §6.12~§6.15。

---

## 5. 变更日志

| 时间 | 操作人/Agent | 说明 |
| --- | --- | --- |
| 2026-06-23 | 初始化 | 创建 F5 任务规划（README/STATUS/PROMPT_DISPATCH + F5-01~09） |
| 2026-06-23 | elk-frontend-agent | F5-01 完成：diagnosis.js 规则 mock + analysis.js 轨迹 mock + 长超时 |
| 2026-06-23 | elk-frontend-agent | F5-05 完成：SuggestionChecklist 可勾选清单 + DiagnosisStageRing node_trace 五阶段映射 |
| 2026-06-23 | elk-frontend-agent | F5-03 完成：ConclusionPanel 双仪表+根因卡+降级角标+空态 |
| 2026-06-23 | elk-frontend-agent | F5-02 完成：DiagnosisEntryPanel 三入口表单+submit payload+query 预填 |
| 2026-06-23 | elk-frontend-agent | F5-07 完成：TraceSearchBar 检索+历史 + TraceWaterfall CSS 泳道瀑布+断点标记 |
| 2026-06-23 | elk-frontend-agent | F5-06 完成：diagnosis.vue 四区装配+submitDiagnosis 提交流+全局 loading/error+route query 预填+规则降级分发 |
| 2026-06-23 | elk-frontend-agent | F5-08 完成：trace.vue searchByTraceId 装配+route query 自动检索+loading/empty/error 态 |
| 2026-06-23 | elk-frontend-agent | F5-09 完成：DEV.md §6.12~6.15 诊断/链路/node_trace/§5 耦合；§8 F5 验收；§10/§12 更新 |
