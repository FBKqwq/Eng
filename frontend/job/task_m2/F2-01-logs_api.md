# F2-01：logs API 扩展 logs_api

## Agent 角色

API 封装专项 Agent — **完善 logs.js 查询、字段目录与聚合契约**。

## 唯一负责文件

```
src/api/logs.js
```

## 禁止修改

- `views/`、`components/`、`composables/`、其他 `api/*.js`（`metrics.js` 只 import `aggregateLogs`）

## 前置依赖

- **前置**：F1-18 = `已完成`/`已合并`（见 `task_m1/STATUS`；截至 2026-06-23 **代码未落地**，须先执行 F1-18 再真实对接）
- 必读：`location/frontend/job/API_CONTRACT.md` §4.2、`backend/app/api/DEV.md` §4.2

## 开发要求

### 1. `searchLogs(payload)` → `POST /logs/search`

请求体对齐 `LogQueryRequest`（**不要用**笼统的 `time_range` 对象替代）：

| 字段 | 说明 |
| --- | --- |
| `start_time` / `end_time` | ISO-8601 **带时区**（UTC 推荐 `...Z`） |
| `log_types[]` | 单个子页固定一类 |
| `service_names[]`、`log_levels[]`、`keyword`、`filters` 等 | 来自 DynamicFilterBar |
| `page` / `page_size` | 分页 |
| `sort_by` / `sort_order` | 排序（默认 `timestamp` desc） |

解包后 `res.data`：`{ items, total, page, page_size, has_more, took_ms }`

失败：`catch (e) { e.error?.code }` → `es_unavailable` 等

### 2. `getLogFields(logType)` → `GET /logs/fields?log_type=`

解包后 `res.data`：

- `{ log_type, catalog: { filter_fields[], terms_fields[], metric_fields[], ... } }`
- 非法类型：reject，`error.code === 'invalid_param'`

### 3. `aggregateLogs(payload)` → `POST /logs/aggregate`

- F1-18 应已存在；本任务验收参数映射与 re-export（若需）
- 解包后：`{ group_by, interval, buckets[], took_ms, extra? }`

### 4. `searchByTraceId(traceId)`

- 内部 `searchLogs({ trace_id, page_size: 500, sort_order: 'asc' })`
- **禁止** `GET /logs/trace/{id}`

### 5. 约束

- wrapper 内不读 `body.ok`；不写 UI
- logs 模块**不使用** `USE_MOCK`（真实接口）

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | search | 请求体含 `start_time/end_time` 与分页排序 |
| AC-02 | fields | 返回 `catalog.filter_fields` 可驱动筛选 |
| AC-03 | aggregate | `aggregateLogs` 可用 |
| AC-04 | trace | `searchByTraceId` 走 search 契约 |
| AC-05 | 信封 | 不读顶层 `ok`；错误用 `e.error?.code` |
| AC-06 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `src/api/logs.js`
- [ ] 更新 `task_m2/STATUS.md` F2-01 行

## 下游消费说明

- F2-02 `useLogQuery` 负责 `useTimeRange` → `start_time/end_time` 映射
- F2-04 读 `catalog.filter_fields`
- F5-08 trace 页调 `searchByTraceId`
