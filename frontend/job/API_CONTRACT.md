# 前端 API 契约基线（全阶段强制）

> **权威来源**：[`location/backend/app/api/DEV.md` §4.2](../../backend/app/api/DEV.md)（2026-06-23 统一信封改造后）
> **机器可读**：`http://localhost:8000/docs`（OpenAPI `ApiResponse[XxxData]`）
> **适用范围**：F1~F7 所有涉及 `src/api/`、composable 调 API、页面读 `res.data` 的任务
> **skill 对齐**：`/elk-frontend-agent` §三「后端契约优先原则」

---

## 1. 请求通道（硬约束）

| 规则 | 说明 |
| --- | --- |
| 唯一入口 | 所有请求经 `src/api/*.js` → `request.js` |
| baseURL | `import.meta.env.VITE_API_BASE_URL`（默认 `http://localhost:8000/api/v1`） |
| 路径写法 | wrapper 内写**相对路径**（如 `/logs/search`），**不要**重复拼 `/api/v1` |
| 禁止直连 | 浏览器不得访问 ES / Kafka / Kibana API |

---

## 2. 统一响应信封与解包（硬约束）

后端全 v1 业务接口返回：

```jsonc
{ "ok": true,  "data": { /* 业务负载 */ }, "error": null }
{ "ok": false, "data": null | 降级数据, "error": { "code": "...", "message": "..." } }
```

**`request.js` 响应拦截器职责**（已实现）：

- `ok === true`：将 `response.data` **替换为** `body.data`（业务负载）
- `ok === false`：`Promise.reject`，`error.error = { code, message }`
- **422 校验失败**：FastAPI 返回 `{ detail: [...] }`，**不走业务信封**，保持 axios 默认结构

**wrapper / 页面约定**：

```javascript
// ✅ 正确：解包后 res.data 即业务负载
const res = await searchLogs(payload)
const items = res.data.items

// ✅ 正确：失败用 catch
try {
  await aggregateLogs(payload)
} catch (e) {
  const code = e.error?.code  // es_unavailable | query_failed | ...
  const msg = e.message
}

// ❌ 错误：wrapper 内再读 body.ok / body.error
// ❌ 错误：页面读 res.data.ok
// ❌ 错误：依赖旧字段 available / placeholder / 顶层 message
```

**`USE_MOCK` 分支约定**：

- mock **必须返回与真实请求解包后相同形态**：`Promise.resolve({ data: <业务负载> })`
- **禁止** mock 返回顶层数组（如 `data: []`），必须与 §4 各接口 `data` 结构一致

---

## 3. 错误码（`ApiCode`）

| code | 典型场景 | 前端建议 |
| --- | --- | --- |
| `es_unavailable` | ES 离线 | EmptyState + 可重试；列表展示空页 |
| `query_failed` | 查询/确认失败 | 错误文案 + 重试 |
| `invalid_param` | 非法 log_type 等 | 表单校验提示 |
| `not_found` | 资源不存在 | 空态（reports 未命中见 §4 特殊规则） |
| `diagnosis_failed` | 诊断失败 | 结论区错误卡 |
| `graph_failed` | 主图执行失败 | 阶段环仍可能带 `data.node_trace` |
| `internal_error` | 服务内部错误 | 通用错误态 |

---

## 4. 接口清单与 `data` 负载（前端必读）

### 4.1 健康与系统

| wrapper 函数 | 方法 | 路径 | 解包后 `res.data` 关键字段 |
| --- | --- | --- | --- |
| `getApiHealth` | GET | `/health` | `{ status: "ok" }` |
| `getSystemStatus` | GET | `/system/status` | `kafka_bootstrap_servers`, `kafka_topic`, `elasticsearch_hosts`, `kafka{available,...}`, `elasticsearch{available,cluster_status,...}`, `docker{available}`, `containers{kafka,elasticsearch,...}`, `services{...}` |
| `getSystemContainers` | GET | `/system/containers` | `{ project, available, error, containers{...} }` |
| `verifyPipeline` | POST | `/system/pipeline/verify` | `PipelineVerifyResponse`（节点状态 + 终端输出；**长超时** ≥210s） |

> **废弃**：读取 `data.available` 作为总开关。改为读 `kafka.available` / `elasticsearch.available` / `docker.available`，失败走 `catch (e.error?.code)`。

### 4.2 日志

| wrapper 函数 | 方法 | 路径 | 解包后 `res.data` |
| --- | --- | --- | --- |
| `searchLogs` | POST | `/logs/search` | `{ items[], total, page, page_size, has_more, took_ms }` |
| `getLogFields` | GET | `/logs/fields?log_type=` | 带参：`{ log_type, catalog{ filter_fields[], terms_fields[], metric_fields[], ... } }`；不带参：`{ registered_log_types[] }` |
| `aggregateLogs` | POST | `/logs/aggregate` | `{ group_by, interval, buckets[{key,count,value?,extra?}], took_ms, extra? }` |

**`LogQueryRequest` 请求体**（`searchLogs`）：

- 时间：`start_time`、`end_time`（**ISO-8601 带时区**，如 `2026-06-22T16:00:00Z`）
- 筛选：`service_names[]`、`log_levels[]`、`log_types[]`、`event_types[]`、`error_codes[]`、`trace_id`、`user_id`、`keyword`、`status_codes[]`
- 分页：`page`（默认 1）、`page_size`（1~500，默认 20）
- 排序：`sort_by`（默认 `timestamp`）、`sort_order`（`asc`/`desc`）

**链路追踪**：**无** `GET /logs/trace/{id}`。使用 `searchLogs({ trace_id, page_size: 500, sort_by: 'timestamp', sort_order: 'asc' })`。

**`LogAggregateRequest` 请求体**（`aggregateLogs`）：

- 必填：`start_time`、`end_time`（跨度 ≤24h）、`group_by`（枚举见后端 `AggregateField`）
- 可选：`log_types[]`、`service_names[]`、`interval`（`1m`/`1h`/`1d`）、`top_n`（默认 10，≤50）、`filters`

**六类聚合模板（业务语义）→ 实现方式**：

| 模板 id | 用途 | 实现 |
| --- | --- | --- |
| `traffic` | 流量趋势 | `metrics.js` 内预制 `LogAggregateRequest` → 调 `aggregateLogs` |
| `errors` | 错误分布 | 同上 |
| `latency` | 耗时趋势 | 同上 |
| `behavior_funnel` | 行为漏斗 | 同上 |
| `security` | 安全分布 | 同上 |
| `infra_health` | 基础设施健康 | 同上 |

> **不存在** `POST /metrics/traffic` 等独立路径（后端 P1「metrics 类接口」未落地）。`metrics.js` 是**模板封装层**，底层统一 `POST /logs/aggregate`。

### 4.3 诊断

| wrapper 函数 | 方法 | 路径 | 解包后 `res.data` |
| --- | --- | --- | --- |
| `submitDiagnosis` | POST | `/diagnosis` | `{ message, input{}, diagnosis{ anomaly_type, severity, route, root_cause, suggestion[], evidence_logs[], context_summary{} } }` |

> **注意**：规则诊断响应**不含** `node_trace`。阶段环数据来自 `GET /reports/{id}` 的 `report.node_trace` 或 `POST /analysis/run` 返回的 `node_trace`（见 §4.5）。

### 4.4 报告与预警

| wrapper 函数 | 方法 | 路径 | 解包后 `res.data` |
| --- | --- | --- | --- |
| `getRecentReports` | GET | `/reports/recent?limit=` | `{ items[{report_id, report_type, title, risk_level, summary, created_at, task_id}], total, limit }` |
| `getReportDetail` | GET | `/reports/{report_id}` | `{ report_id, report{完整报告含 node_trace} }`；未命中：`report: null`（**仍 200**） |
| `getActiveAlerts` | GET | `/alerts/active?limit=` | `{ items[{alert_id, alert_type, severity, status, title, affected_service, evidence_count, created_at, updated_at}], total }` |
| `acknowledgeAlert` | POST | `/alerts/{alert_id}/ack` | `{ alert_id, status: "acknowledged" }` |

**角标计数**：`alertCount = data.total ?? data.items?.length ?? 0`（**不是**顶层数组长度）。

### 4.5 分析轨迹（新增 wrapper 文件）

| wrapper 函数 | 方法 | 路径 | 解包后 `res.data` |
| --- | --- | --- | --- |
| `getRecentAnalysisRuns` | GET | `/analysis/runs/recent?limit=` | `{ items[{report_id, report_type, title, created_at, trigger_type, node_trace[{node_name,status,duration_ms,output_summary}], node_count, total_duration_ms}], total, limit }` |
| `triggerAnalysisRun` | POST | `/analysis/run` | `{ report_id, alert_id, node_trace[], alert_decision{}, errors[] }`（**同步长耗时**） |

**落点**：`src/api/analysis.js`（F1-18 或 F5 阶段新建）。

---

## 5. mock 契约化空数据（`USE_MOCK=true` 时）

| 模块 | 正确 mock `data` 形态 |
| --- | --- |
| `aggregateLogs` / metrics 模板 | `{ group_by: 'service_name', buckets: [], took_ms: 0 }` |
| `getRecentReports` | `{ items: [], total: 0, limit: 20 }` |
| `getReportDetail` | `{ report_id: null, report: null }` |
| `getActiveAlerts` | `{ items: [], total: 0 }` |
| `acknowledgeAlert` | `{ alert_id: '<id>', status: 'acknowledged' }` |
| `getRecentAnalysisRuns` | `{ items: [], total: 0, limit: 20 }` |

---

## 6. 各阶段 API 任务对照

| 阶段 | 主要 API 任务 | 契约要点 |
| --- | --- | --- |
| F1-03 / **F1-18** | 7+1 个 api 文件 + 信封解包 | mock 形态、去除 `/metrics/*`、去除 `/logs/trace` |
| F2-01 | `logs.js` 扩展 | `searchLogs` 字段名、`getLogFields` catalog 结构、`searchByTraceId` |
| F3-01 | `system.js` | status 嵌套字段、verify 长超时 |
| F4-01 | `metrics.js` | 六模板 → `aggregateLogs`，非 `/metrics/*` |
| F5-01 | `diagnosis.js` + `analysis.js` | 诊断 vs 轨迹数据源分离 |
| F6-01/02 | `reports.js` / `alerts.js` | `USE_MOCK=false`；items+total |
| F6-07 | TopBar 等 | `data.total` 角标 |

---

## 7. 任务文档维护约定

- 各 `FN-xx-*.md` 涉及 API 时，必须引用本文档 §4 对应表，**不得**自造路径或旧信封字段。
- 后端契约变更时，**先更新** `backend/app/api/DEV.md` §4.2，再同步本文档与各阶段 api 任务。
- 代码审查自检：mock 返回形态、页面不读 `ok`、无 `available`/`placeholder` 依赖。
