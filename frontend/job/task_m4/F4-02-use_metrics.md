# F4-02：聚合组合式 use_metrics

## Agent 角色

组合式逻辑 Agent — **统一 metrics 查询、时间窗联动与状态**。

## 唯一负责文件

```
src/composables/useMetrics.js
```

## 禁止修改

- api、views、components

## 前置依赖

- F4-01 `metrics.js` 六函数就绪
- F1-02 `useTimeRange`

## 开发要求

### 1. API 设计

```javascript
useMetrics({ template, logType?, extraFilters?, immediate? })
```

- 返回：`{ data, loading, error, refresh, isMock }`
- `template` 枚举六类之一

### 2. 时间窗联动

- inject `useTimeRange`
- `range` 变更自动 `refresh`（debounce 300ms）

### 3. mock 感知

- 当 `metrics.USE_MOCK === true` 时 `isMock=true`，供 UI 展示「演示数据」角标

### 4. 错误态

- 不抛未捕获异常；`error` 供 EmptyState 使用

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 联动 | 时间窗变更触发重查 |
| AC-02 | 六模板 | template 参数映射正确 |
| AC-03 | 状态 | loading/error/data 齐全 |
| AC-04 | isMock | mock 开关可感知 |

## 完成定义（DoD）

- [ ] 仅新建/修改 `useMetrics.js`
- [ ] 更新 STATUS F4-02 行

## 下游消费说明

- F4-03 ChartBand、F4-05~08 各图表区
