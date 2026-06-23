# F6-01：reports API 扩展 reports_api

## Agent 角色

API 封装专项 Agent — **完善 reports.js，关闭 mock，对齐信封解包后 `data` 结构**。

## 唯一负责文件

```
src/api/reports.js
```

## 禁止修改

- views、components、其他 api

## 前置依赖

- **前置**：F1-18 = `已完成`/`已合并`（见 `task_m1/STATUS`；mock 形态须在 F1-18 修正）
- 必读：`API_CONTRACT.md` §4.4；后端 M4 已真实对接

## 开发要求

### 1. `getRecentReports(params?)`

- `GET /reports/recent?limit=`（limit 1~100，默认 20）
- 解包后 `res.data`：`{ items[{ report_id, report_type, title, risk_level, summary, created_at, task_id }], total, limit }`

### 2. `getReportDetail(reportId)`

- `GET /reports/{report_id}`
- 解包后 `res.data`：`{ report_id, report: { ...含 node_trace, sections, metrics_snapshot } }`
- **未命中**：`ok:true` 且 `report: null`（200，非 404）→ 页面展示空态

### 3. `USE_MOCK`

- 后端 M4 已就绪：**默认 `USE_MOCK = false`**
- mock 仅开发离线：`items+total+limit` / `report:null` 结构

### 4. 错误处理

- `query_failed`：`catch` 展示错误态
- wrapper 不读 `body.ok`

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 列表 | `data.items` 数组 + `data.total` |
| AC-02 | 详情 | `data.report` 含 `node_trace` |
| AC-03 | 未命中 | `report:null` 不抛 404 |
| AC-04 | mock关 | 默认 `USE_MOCK=false` |
| AC-05 | 构建 | 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `reports.js`
- [ ] 更新 STATUS F6-01 行

## 下游消费说明

- F6-03/04/07
