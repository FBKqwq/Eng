# F5-08：链路页装配 trace_view

## Agent 角色

页面装配 Agent — **trace 数据拉取与组件组合**。

## 唯一负责文件

```
src/views/analysis/trace.vue
```

## 禁止修改

- TraceSearchBar、TraceWaterfall（只组合）
- api 文件（只调 `searchByTraceId`）

## 前置依赖

- F5-07 组件
- `logs.js` `searchByTraceId`

## 开发要求

### 1. 路由

- 读取 `route.query.trace_id` 自动搜索
- 与 F2 `/analysis/trace?trace_id=` 对齐

### 2. 数据流

- 搜索 → `searchByTraceId` → 取 `res.data.items` 传给 Waterfall
- ES 离线：`catch` → `e.error?.code === 'es_unavailable'` 错误态
- loading / empty / error 态

### 3. 约束

- 不暴露 ES 直连

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 带参跳入 | query trace_id 自动查 |
| AC-02 | 手动搜 | 输入框搜索可用 |
| AC-03 | 错误 | 无效 id 有错误态 |
| AC-04 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `trace.vue`
- [ ] 更新 STATUS F5-08 行

## 下游消费说明

- 监控页、诊断页跳转入口
