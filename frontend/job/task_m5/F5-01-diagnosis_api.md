# F5-01：诊断与分析 API diagnosis_analysis_api

## Agent 角色

API 封装专项 Agent — **完善 diagnosis.js 与 analysis.js**。

## 唯一负责文件

```
src/api/diagnosis.js
src/api/analysis.js
```

## 禁止修改

- views、components、其他 api

## 前置依赖

- **前置**：F1-18 = `已完成`/`已合并`（见 `task_m1/STATUS`；**代码未落地**则阻塞）
- 必读：`API_CONTRACT.md` §4.3、§4.5

## 开发要求

### 1. `diagnosis.js` — `submitDiagnosis(payload)`

- `POST /diagnosis`
- 请求：`request_id` 必填；常用 `keyword` / `service_name` / `error_code` / `time_range_start` / `time_range_end`
- 解包后 `res.data`：
  ```jsonc
  { message, input{}, diagnosis{ anomaly_type, severity, route, root_cause, suggestion[], evidence_logs[], context_summary{} } }
  ```
- **不含 `node_trace`**（规则诊断门面）

### 2. `analysis.js`

| 函数 | 路径 | 解包后 `data` |
| --- | --- | --- |
| `getRecentAnalysisRuns(params)` | `GET /analysis/runs/recent` | `{ items[{..., node_trace[]摘要}], total, limit }` |
| `triggerAnalysisRun(payload)` | `POST /analysis/run` | `{ report_id, alert_id, node_trace[], alert_decision{}, errors[] }` |

- `triggerAnalysisRun`：**timeout ≥ 120000ms**（同步长耗时）
- `graph_failed` 时 `catch` 但 `data` 可能仍含 `node_trace`

### 3. Mock（可选 `USE_MOCK`）

- diagnosis mock 含规则降级样例（`route: 'rule'`）
- analysis mock 含 `node_trace` 摘要条目（`node_name/status/duration_ms`）

### 4. 约束

- 不写 UI；不读 `body.ok`

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | diagnosis | `data.diagnosis` 字段齐全 |
| AC-02 | analysis | 两函数导出且路径正确 |
| AC-03 | node_trace | 文档注明诊断响应无 node_trace |
| AC-04 | 超时 | analysis/run 长超时配置 |
| AC-05 | 构建 | 通过 |

## 完成定义（DoD）

- [ ] 仅修改上述两 api 文件
- [ ] 更新 STATUS F5-01 行

## 下游消费说明

- F5-05 阶段环：`triggerAnalysisRun` 或 `getReportDetail` 的 `report.node_trace`
- F5-06 诊断页组装
