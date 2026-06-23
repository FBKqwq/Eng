# F6-02：alerts API 扩展 alerts_api

## Agent 角色

API 封装专项 Agent — **完善 alerts.js，关闭 mock，对齐 `items+total` 契约**。

## 唯一负责文件

```
src/api/alerts.js
```

## 禁止修改

- views、components、其他 api

## 前置依赖

- **前置**：F1-18 = `已完成`/`已合并`（见 `task_m1/STATUS`；mock 形态须在 F1-18 修正）
- 必读：`API_CONTRACT.md` §4.4；后端 M5 已真实对接

## 开发要求

### 1. `getActiveAlerts(params?)`

- `GET /alerts/active?limit=`（1~200，默认 50）
- 解包后 `res.data`：`{ items[{ alert_id, alert_type, severity, status, title, affected_service, evidence_count, created_at, updated_at }], total }`
- **角标计数**：消费方用 `data.total`（TopBar F6-07）

### 2. `acknowledgeAlert(alertId, body?)`

- `POST /alerts/{alert_id}/ack`
- body 可选 `{ operator }`
- 解包后 `res.data`：`{ alert_id, status: 'acknowledged' }`
- 失败：`error.code === 'query_failed'`

### 3. `USE_MOCK`

- 默认 **`USE_MOCK = false`**
- mock：`{ items: [], total: 0 }`（**禁止** `data: []`）

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | active | `data.items` + `data.total` |
| AC-02 | ack | 返回 `alert_id` + `status` |
| AC-03 | mock | 形态非顶层数组 |
| AC-04 | 构建 | 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `alerts.js`
- [ ] 更新 STATUS F6-02 行

## 下游消费说明

- F6-05/06/07、TopBar 轮询
