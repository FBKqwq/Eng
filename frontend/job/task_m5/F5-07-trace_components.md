# F5-07：链路组件 trace_components

## Agent 角色

链路可视化 Agent — **检索栏 + 泳道瀑布图**。

## 唯一负责文件

```
src/components/analysis-trace/TraceSearchBar.vue
src/components/analysis-trace/TraceWaterfall.vue
```

## 禁止修改

- api、views、charts 底层

## 前置依赖

- F2-01 / F1-18 `searchByTraceId(traceId)`（内部 `POST /logs/search` + `trace_id`）
- F2 LogTable 跳转 query 约定

## 开发要求

### 1. TraceSearchBar

- trace_id 输入 + 搜索按钮
- 最近查询历史（localStorage，≤10 条）
- 支持 props 初始 `traceId`（来自 route）

### 2. TraceWaterfall

- 同 trace 日志按时间排序
- 泳道：每服务一条；日志块按时间定位
- ERROR 块红色；点击展开原始字段
- 顶部摘要：总耗时、服务数、断点红色标记

### 3. 约束

- 不调 API（由 view 传入 logs）
- 不用 echarts 瀑布（CSS/DOM 泳道实现）

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 检索 | 输入 trace_id 可搜索 |
| AC-02 | 历史 | 最近查询可复用 |
| AC-03 | 瀑布 | 泳道与 ERROR 着色 |
| AC-04 | 断点 | 链路中断有标记 |

## 完成定义（DoD）

- [ ] 仅修改上述两个 vue 文件
- [ ] 更新 STATUS F5-07 行

## 下游消费说明

- F5-08 `trace.vue`
