# F2-03：日志明细表 LogTable

## Agent 角色

通用组件 Agent — **实现可配置日志表格**（分页/排序/行展开/trace 跳转）。

## 唯一负责文件

```
src/components/common/LogTable.vue
```

## 禁止修改

- `charts/`、monitor 组件、views、api

## 前置依赖

- F2-02 约定 props/events 契约（可与 F2-06 对齐接口）
- F1-06 EmptyState、SeverityBadge 可复用

## 开发要求

### 1. Props

| 属性 | 说明 |
| --- | --- |
| `columns` | `{ key, label, width?, sortable? }[]` |
| `items` | 行数据数组 |
| `total` | 总条数 |
| `page` / `pageSize` | 分页 |
| `loading` / `error` | 状态 |
| `sort` | 当前排序 `{ field, order }` |

### 2. Events

- `update:page`、`update:pageSize`、`sort-change`
- `trace-navigate(traceId)` — 含 trace_id 列提供跳转按钮

### 3. 交互

- 行点击或展开图标展示完整字段 JSON（折叠面板）
- 级别列用 `SeverityBadge`
- 加载用骨架行；错误用 `EmptyState` + 重试 emit
- `tabular-nums` 数字列

### 4. 约束

- 不直接调 api；纯展示 + emit
- 尊重 `prefers-reduced-motion`

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 分页 | 翻页 emit 正确 |
| AC-02 | 排序 | sortable 列 emit sort-change |
| AC-03 | 展开 | 行展开显示完整字段 |
| AC-04 | trace | trace_id 可触发跳转事件 |
| AC-05 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `LogTable.vue`
- [ ] 更新 STATUS F2-03 行

## 下游消费说明

- F2-06 Shell 组装；路由跳转由 Shell 或 view 处理
