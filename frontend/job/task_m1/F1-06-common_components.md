# F1-06：通用展示基础件 common_components

## Agent 角色

通用组件专项 Agent — **仅实现非图表类通用展示组件**（空态、卡片、徽章、表格占位、时间轴、阶段环）。

## 唯一负责文件

```
src/components/common/EmptyState.vue
src/components/common/StatCard.vue
src/components/common/StatusCard.vue
src/components/common/SeverityBadge.vue
src/components/common/LogTable.vue
src/components/common/TimeAxis.vue
src/components/common/StageRing.vue
```

## 禁止修改

- `components/common/charts/`（归 F1-05）
- 其他任何文件

## 前置依赖

- F1-01 设计令牌（配色/卡片/语义色复用）

## 开发要求

### 1. `EmptyState.vue`（统一占位/空态）

- props：`title`、`description`、`pendingApi`（标注待接入接口）、`compact`（紧凑模式）。
- 这是 F1 阶段所有未实现业务区块的统一占位载体。

### 2. 其他通用件（F1 阶段可为占位/空壳，结构就位即可）

| 组件 | F1 要求 |
| --- | --- |
| `StatCard.vue` | 数字指标卡：`label`、`value`、`hint`（无值显示占位） |
| `StatusCard.vue` | 组件状态卡：`title`、`statusLabel`（由 ServiceStatusCard 通用化的目标，F1 仅骨架） |
| `SeverityBadge.vue` | 级别/严重度徽章：级别配色唯一出处，复用语义色令牌 |
| `LogTable.vue` | 日志表格占位：内部用 `EmptyState`，`pending-api="POST /api/v1/logs/search"`（真实表格留待 F2） |
| `TimeAxis.vue` | 垂直时间轴占位（证据链/报告轴复用） |
| `StageRing.vue` | 阶段环/步骤条占位（`node_trace` 可视化唯一载体，留待 F5 接数据） |

### 3. 约束（强制）

- **通用组件准入**：进入 `common/` 的前提是「将被 ≥2 个页面使用」，本批均满足。
- 不在组件内发请求；不直接 `import echarts`（需要图表时由页面组合 charts 组件）。
- 简体中文注释与占位文案。

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | EmptyState | 支持 title/description/pendingApi/compact |
| AC-02 | SeverityBadge | 级别配色取自语义色令牌 |
| AC-03 | LogTable | F1 显示占位空态，不报错 |
| AC-04 | 7 组件 | 全部可独立挂载，构建通过 |

## 完成定义（DoD）

- [ ] 仅修改 common/ 下 7 个非图表组件
- [ ] 不修改 DEV.md

## 下游消费说明（供其他 Agent 只读）

- F1-12~15 各页面占位大量复用 `EmptyState`
- F1-08 SidebarTree 与各页可复用 `SeverityBadge`/`StatCard`
