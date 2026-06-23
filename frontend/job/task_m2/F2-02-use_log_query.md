# F2-02：日志查询组合式 use_log_query

## Agent 角色

Composable 专项 Agent — **统一监控页查询状态机**（筛选/分页/排序/加载/错误）。

## 唯一负责文件

```
src/composables/useLogQuery.js（新建）
```

## 禁止修改

- 其他任何文件

## 前置依赖

- F2-01 `searchLogs` 可用
- F1-02 `useTimeRange` 已就位（本 composable 内 inject 时间窗）

## 开发要求

### 1. 导出 `useLogQuery(logType)`

状态：

- `loading`、`error`、`items`、`total`
- `page`、`pageSize`、`sort`、`keyword`、`filters`（对象）

方法：

- `fetch()` — 合并时间窗 + 筛选 + 分页调用 `searchLogs`
- `setPage(n)`、`setSort(field, order)`、`setKeyword(k)`、`setFilters(obj)`、`resetFilters()`
- 监听 `useTimeRange` 的 range 变化自动 `fetch`（debounce 可选，≤300ms）
- 将 range 映射为 API 要求的 `start_time` / `end_time`（ISO-8601 UTC，见 `API_CONTRACT.md` §4.2）
- 错误：`catch (e) { e.error?.code }`，`es_unavailable` 时展示空页+重试

### 2. 默认

- `pageSize` 默认 20；`sort` 默认 `@timestamp desc`

### 3. 约束

- 不 import 任何 `.vue`；不直接 axios
- onUnmounted 取消未完成请求（AbortController 或标志位）

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 状态 | 暴露 loading/error/items/total |
| AC-02 | 时间窗 | range 变更触发重查 |
| AC-03 | 分页 | setPage 后 fetch 带正确 page |
| AC-04 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅新增/修改 `useLogQuery.js`
- [ ] 更新 STATUS F2-02 行

## 下游消费说明

- F2-06 `LogMonitorShell` 调用本 composable
