# F2-06：监控骨架编排 LogMonitorShell

## Agent 角色

监控骨架 Agent — **串联筛选区、图表占位、明细表与查询逻辑**。

## 唯一负责文件

```
src/components/monitor/LogMonitorShell.vue
```

## 禁止修改

- `ChartBand.vue`（F1/F4 负责）、`DynamicFilterBar.vue`、`LogTable.vue`（只组合）
- `views/monitor/`、api 文件

## 前置依赖

- F2-02 `useLogQuery`
- F2-03 `LogTable`
- F2-04 `DynamicFilterBar`

## 开发要求

### 1. Props

- `logType` — 传给子组件与 composable

### 2. 布局（三段式）

```text
[DynamicFilterBar] — v-model 筛选/关键字，变更 debounce 后 fetch
[ChartBand]        — 仍传 chartTemplates from meta，F2 不改动 ChartBand 内部
[LogTable]         — 绑定 useLogQuery 状态与事件
```

### 3. trace 跳转

- `LogTable` 的 trace 事件 → `router.push({ path: '/analysis/trace', query: { trace_id } })`

### 4. 约束

- 不修改 `ChartBand.vue` 源码
- 首次 mount 自动 fetch

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 串联 | 筛选变更触发查询 |
| AC-02 | 表格 | LogTable 展示真实数据或错误态 |
| AC-03 | 图表 | ChartBand 仍为占位 |
| AC-04 | trace | 跳转链路页带 query |
| AC-05 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `LogMonitorShell.vue`
- [ ] 更新 STATUS F2-06 行
