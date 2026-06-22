# F1-03：API wrapper 骨架 api_wrappers

## Agent 角色

API 封装专项 Agent — **仅建立 7 个请求 wrapper 与 mock 开关**，不在页面接入。

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

- 无（须对齐 `location/frontend/前端开发总体规划.md` §6 API 契约表）

## 开发要求

### 1. `request.js`

- axios 实例：`baseURL` 取 `import.meta.env.VITE_API_BASE_URL`。
- 统一请求/响应拦截器与错误处理。

### 2. 已有后端接口（真实请求）

| wrapper | 方法与路径 |
| --- | --- |
| `logs.js` | `POST /logs/search`、`GET /logs/recent`、`GET /logs/trace/{id}`、`GET /logs/fields?log_type=` |
| `diagnosis.js` | `POST /diagnosis` |
| `system.js` | `GET /health`、`GET /system/status`、`POST /system/pipeline/verify` |

### 3. 待后端接口（先落 wrapper + `USE_MOCK`）

每个文件顶部导出 `export const USE_MOCK = true`，开启时返回契约化空数据，关闭时走真实 `request`。

| wrapper | 方法与路径 | mock 返回 |
| --- | --- | --- |
| `metrics.js` | `POST /metrics/{traffic,errors,latency,behavior_funnel,security,infra_health}` | `{ buckets: [], series: [], total: 0 }` |
| `reports.js` | `GET /reports/recent`、`GET /reports/{id}` | `[]` / `null` |
| `alerts.js` | `GET /alerts/active`、`POST /alerts/{id}/ack` | `[]` / `{ id, status: 'acknowledged' }` |

### 4. 约束

- mock 数据形态严格按后端 schema 契约；后端就绪后只改 `USE_MOCK` 开关，不改页面。
- 不在 wrapper 内写业务/渲染逻辑。
- 简体中文注释。

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 实例 | `request.js` 正确读取 `VITE_API_BASE_URL` |
| AC-02 | 真实接口 | logs/diagnosis/system 走真实 `request` |
| AC-03 | mock 开关 | metrics/reports/alerts 含 `USE_MOCK` 且默认 `true` |
| AC-04 | 契约 | mock 返回结构与后端 schema 一致（空集合） |

## 完成定义（DoD）

- [ ] 仅修改上述 7 个 api 文件
- [ ] 不修改 DEV.md

## 下游消费说明（供其他 Agent 只读）

- F1-09 TopBar 调 `getActiveAlerts`
- F1-10 PipelineHealthDot 调 `getSystemStatus`
- F1-12~15 各页面占位组件可 import 对应 wrapper 备用（F1 不强制接入渲染）
