# F1-03：API wrapper 骨架 api_wrappers

## Agent 角色

API 封装专项 Agent — **建立 api 层骨架与 mock 开关**（F1 追溯任务；**契约细节以 F1-18 与 `API_CONTRACT.md` 为准**）。

## 唯一负责文件

```
src/api/request.js
src/api/logs.js
src/api/metrics.js
src/api/diagnosis.js
src/api/reports.js
src/api/alerts.js
src/api/system.js
```

## 禁止修改

- `views/`、`components/`、`layout/`、`composables/`、`utils/`

## 前置依赖

- 必读：`location/frontend/job/API_CONTRACT.md`、`location/backend/app/api/DEV.md` §4.2

## 开发要求

### 1. `request.js`

- `baseURL` = `import.meta.env.VITE_API_BASE_URL`
- **响应拦截器解包信封** `{ ok, data, error }`：`ok===true` 时 `response.data = body.data`；失败 reject 并附 `error.error`
- 422 校验错误保持 axios `{ detail }` 结构

### 2. 真实接口 wrapper（走 `request`）

| 文件 | 方法与路径 | 解包后 `res.data` 要点 |
| --- | --- | --- |
| `logs.js` | `POST /logs/search` | `{ items, total, page, page_size, has_more, took_ms }` |
| `logs.js` | `GET /logs/fields?log_type=` | `{ log_type, catalog }` 或 `{ registered_log_types }` |
| `logs.js` | `POST /logs/aggregate` | `{ group_by, buckets[], took_ms }` |
| `diagnosis.js` | `POST /diagnosis` | `{ message, input, diagnosis{...} }` |
| `system.js` | `GET /health`、`GET /system/status`、`POST /system/pipeline/verify` | 见 API_CONTRACT §4.1 |

### 3. `USE_MOCK` 模块（mock 形态必须对齐 `data` 负载）

| 文件 | 真实路径 | mock 时 `Promise.resolve({ data })` 形态 |
| --- | --- | --- |
| `metrics.js` | 经 `aggregateLogs` 六模板封装 | `{ group_by, buckets: [], took_ms: 0 }` |
| `reports.js` | `GET /reports/recent`、`GET /reports/{id}` | `{ items:[], total:0, limit:20 }` / `{ report_id:null, report:null }` |
| `alerts.js` | `GET /alerts/active`、`POST /alerts/{id}/ack` | `{ items:[], total:0 }` / `{ alert_id, status:'acknowledged' }` |

### 4. 禁止项

- ❌ `POST /metrics/*`（路径不存在）
- ❌ `GET /logs/trace/{id}`（用 `searchLogs({ trace_id })`）
- ❌ mock 返回顶层数组 `data: []`
- ❌ wrapper 内读取 `body.ok` / 依赖 `available` / `placeholder`

### 5. 约束

- 不在 wrapper 内写渲染逻辑
- 简体中文注释

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 信封 | `request.js` 解包符合 API_CONTRACT §2 |
| AC-02 | 真实接口 | logs/diagnosis/system 路径正确 |
| AC-03 | mock | metrics/reports/alerts 含 `USE_MOCK` 且 mock 形态为 `items+total` 等契约结构 |
| AC-04 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改上述 api 文件（**或**由 F1-18 统一回补）
- [ ] 不修改 DEV.md（F1-17）

## 下游消费说明

- **F1-18** 对追溯落地的 api 做契约复审与修正
- F1-09 `getActiveAlerts` → 读 `data.total` 或 `data.items.length`
- F1-10 `getSystemStatus` → 读嵌套 `kafka.available` 等

> **状态说明**：F1 追溯已落地骨架；若 mock 形态或 `/metrics/*` 仍存在，由 **F1-18** 收口，不以本任务重复改码。
