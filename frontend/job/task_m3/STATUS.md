# F3 任务进度与依赖状态（Agent 共享真相源）

> **用途**：各 Agent 开工前必读本文；任务完成后仅更新**自己负责的那一行**。
> **静态编排**：见 `README.md`、`PROMPT_DISPATCH.md`
> **任务细则**：见 `F3-xx-*.md`
> **强制基线**：`location/frontend/前端开发总体规划.md`
> **前置里程碑**：F1 全部 `已完成`/`已合并`（尤其 F1-15 系统占位、F1-03 system api、F1-10 健康点）

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
| F3-01 | F1-03 = `已完成`/`已合并` |
| F3-02 | F1 = `已完成`/`已合并` |
| F3-03 | F3-02 = `已完成`/`已合并` |
| F3-04 | F3-01 = `已完成`/`已合并` |
| F3-05 | F3-03、F3-04 = `已完成`/`已合并` |
| F3-06 | F1-06 = `已完成`/`已合并` |
| F3-07 | F3-01、F3-02、F3-06 = `已完成`/`已合并` |
| F3-08 | F3-01 = `已完成`/`已合并` |
| F3-09 | F3-08 = `已完成`/`已合并` |
| F3-10 | F3-01 ~ F3-09 均为 `已完成`/`已合并` |

---

## 3. 任务状态表

| 任务 | 负责文件/目录 | 状态 | 负责人/Agent | 完成时间 | 分支/PR | 验收摘要 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F3-01 | `api/system.js` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~04 通过：getSystemStatus 嵌套契约注释、verifyPipeline workers 默认 2、getHealth/getApiHealth 兼容、build OK | — |
| F3-02 | `utils/systemStatus.js` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~04 通过：normalizeComponents、getPipelineNodes、derivePipelineHealthTone、ES unknown 兜底、build OK | PipelineHealthDot/components 已消费 |
| F3-03 | `components/system/PipelineGraph.vue` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~04 通过：四节点横向链路、状态色过渡、loading 骨架、build OK | — |
| F3-04 | `components/system/VerifyOutputPanel.vue` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~04 通过：workers 参数、等宽输出折叠、running/error 态、build OK | — |
| F3-05 | `views/system/pipeline.vue` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~04：status→PipelineGraph、verify→VerifyOutputPanel、错误态+重试、build OK | F7-05 粒子背板已挂载 |
| F3-06 | `components/common/StatusCard.vue` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~04 通过：通用状态卡、四态色、port/container/detail、loading 骨架、build OK | — |
| F3-07 | `views/system/components.vue` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~04 通过：六组件矩阵、60s 轮询、ES 兜底横幅、build OK | — |
| F3-08 | `components/system/ConfigSnapshotCard.vue` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~04 通过：分组 KV 只读、敏感脱敏、Kibana/Discover 双入口 props、build OK | F7-03 discoverUrl 已接线 |
| F3-09 | `views/system/config.vue` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~04：status→groups 映射、kibanaLinks 消费、缺失「未配置」、错误 EmptyState+重试、build OK | — |
| F3-10 | `frontend/DEV.md` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~04 通过：§6.5 系统三页、§7 兜底规则、§12 F3 开发日志已收敛 | **F3 里程碑可收口** |

---

## 4. 当前可派发任务

| 可派发任务 | 原因 |
| --- | --- |
| — | **F3 已全部完成** |

> F3 与 F2 可并行开发（目录不重叠）；系统运维三页已真实对接 status/verify。

---

## 5. 变更日志

| 时间 | 操作人/Agent | 说明 |
| --- | --- | --- |
| 2026-06-23 | 初始化 | 创建 F3 任务规划（README/STATUS） |
| 2026-06-23 | 补全 | 新增 PROMPT_DISPATCH + F3-01~10 任务细则 |
| 2026-06-23 | F3-01 | system.js 扩展 getSystemStatus/verifyPipeline(workers)/getHealth 契约 |
| 2026-06-23 | elk-frontend-agent | 追溯验收：F3-02~08 代码已落地；config 接入 kibanaLinks；STATUS 全表收口 |
