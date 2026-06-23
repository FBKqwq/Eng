# F1-18：API 契约回补 api_contract_retrofit

## Agent 角色

API 契约专项 Agent — **按统一信封与 `API_CONTRACT.md` 回补现有 api 层**，不修改页面/组件。

## 唯一负责文件

```
src/api/request.js          ← 仅验收/补注释，结构已正确则不改逻辑
src/api/logs.js
src/api/metrics.js
src/api/diagnosis.js
src/api/reports.js
src/api/alerts.js
src/api/system.js
src/api/analysis.js         ← 新建
```

## 禁止修改

- `views/`、`components/`、`layout/`、`composables/`、`utils/`

## 前置依赖

- F1-03 骨架已存在（追溯完成）
- **必读**：`location/frontend/job/API_CONTRACT.md`、`location/backend/app/api/DEV.md` §4.2

## 开发要求

### 1. `request.js` 验收

- 确认拦截器：`ok===true` → `response.data = body.data`；`ok===false` → reject + `error.error`
- 422 保持 axios 默认；注释说明页面 `catch` 用法

### 2. `logs.js`

| 函数 | 要求 |
| --- | --- |
| `searchLogs` | `POST /logs/search`，保留 |
| `getLogFields` | `GET /logs/fields`，保留 |
| `aggregateLogs` | **新增** `POST /logs/aggregate` |
| `searchByTraceId` | **新增**：内部调 `searchLogs({ trace_id, page_size: 500, sort_by: 'timestamp', sort_order: 'asc' })` |
| ~~`getLogTrace`~~ | **删除或废弃**（后端无此路由） |
| ~~`getRecentLogs`~~ | 若无后端路由则删除；需要「最近日志」用 `searchLogs` 默认排序 |

### 3. `metrics.js`（模板封装层）

- **删除** `POST /metrics/*` 调用
- 六函数内部组装 `LogAggregateRequest` 并调 `aggregateLogs`（从 logs.js import）
- `USE_MOCK=true` 时返回：`{ data: { group_by: '...', buckets: [], took_ms: 0 } }`（**无** `series`/`total` 自创字段）
- 各模板预制参数对齐 `aggregation_service` 语义（traffic/errors/latency/behavior_funnel/security/infra_health）

### 4. `reports.js` / `alerts.js`

- mock `data` 改为契约形态：
  - reports：`{ items: [], total: 0, limit: 20 }`
  - alerts active：`{ items: [], total: 0 }`
  - ack：`{ alert_id, status: 'acknowledged' }`
- `getReportDetail` mock：`{ report_id: null, report: null }`

### 5. `diagnosis.js`

- 保留 `submitDiagnosis` → `POST /diagnosis`
- 补充 JSDoc：解包后 `data.diagnosis` 结构（无 `node_trace`）

### 6. `analysis.js`（新建）

- `getRecentAnalysisRuns(params)` → `GET /analysis/runs/recent`
- `triggerAnalysisRun(payload)` → `POST /analysis/run`（**长超时** ≥120s）

### 7. `system.js`

- 保持现有三函数；可选新增 `getSystemContainers` → `GET /system/containers`

### 8. 约束

- wrapper 内**不得**读 `body.ok`（交给 request 拦截器）
- mock 返回 `Promise.resolve({ data: <业务负载> })`，形态与解包后一致
- 简体中文注释；不写 UI 逻辑

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 信封 | 真实请求解包后 `res.data` 为业务负载 |
| AC-02 | logs | 含 `aggregateLogs`、`searchByTraceId`；无 `/logs/trace` |
| AC-03 | metrics | 六模板调 `aggregateLogs`；无 `/metrics/*` |
| AC-04 | mock | reports/alerts mock 为 `items+total` 结构 |
| AC-05 | analysis | `analysis.js` 两函数导出 |
| AC-06 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改上述 api 文件
- [ ] 更新 `task_m1/STATUS.md` F1-18 行
- [ ] 在 F1-03 行备注「已由 F1-18 契约复审」

## 下游消费说明

- F2-01 可聚焦 composable 映射，不必重复修 api
- F4-01 在 F1-18 后主要为 `USE_MOCK=false` 与模板参数微调
- F5-01 可聚焦 diagnosis mock 样例与 analysis 联调
- F6-01/02 主要为 `USE_MOCK=false`
