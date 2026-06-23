# F4-01：聚合 API 扩展 metrics_api

## Agent 角色

API 封装专项 Agent — **完善 metrics.js 六类业务模板封装**（底层统一 `POST /logs/aggregate`）。

## 唯一负责文件

```
src/api/metrics.js
```

## 禁止修改

- views、components、composables、`logs.js`（只 import `aggregateLogs`）

## 前置依赖

- **前置**：F1-18 = `已完成`/`已合并`（见 `task_m1/STATUS`；**代码未落地**则阻塞）
- 必读：`API_CONTRACT.md` §4.2 六模板表、`backend/app/api/DEV.md` `LogAggregateRequest`

## 开发要求

### 1. 架构（重要）

```
metrics.js 六模板函数
    → 组装 LogAggregateRequest（start_time/end_time/group_by/interval/log_types/...）
    → logs.aggregateLogs(payload)
    → res.data = { group_by, buckets[], took_ms }
```

**不存在** `POST /metrics/traffic` 等路径。

### 2. 开关

- `export const USE_MOCK = false`（后端 M1 `/logs/aggregate` 已落地；离线调试可临时 true）
- mock：`Promise.resolve({ data: { group_by: '<field>', buckets: [], took_ms: 0 } })`

### 3. 六模板函数

| 函数 | 业务模板 | 典型 group_by / log_types / interval |
| --- | --- | --- |
| `queryTraffic` | traffic | application+web_server；时间直方图 |
| `queryErrors` | errors | error_code / status_code 等 |
| `queryLatency` | latency | 耗时相关 group_by |
| `queryBehaviorFunnel` | behavior_funnel | behavior 类 event_type 步骤 |
| `querySecurity` | security | security 类 risk 字段 |
| `queryInfraHealth` | infra_health | infrastructure 组件健康 |

> 各函数 payload 入参至少含时间窗；具体 `group_by` 与 `logTypeMeta.chartTemplates`（F4-04）对齐。

### 4. 约束

- 不读 `body.ok`；错误交给 `catch (e.error?.code)`
- 禁止 mock 返回 `series`/`total` 等非契约顶层字段

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 六模板 | 6 函数均调 `aggregateLogs` |
| AC-02 | 无伪路径 | 无 `/metrics/*` 字符串 |
| AC-03 | USE_MOCK | mock 形态为 `{ group_by, buckets, took_ms }` |
| AC-04 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `metrics.js`
- [ ] 更新 STATUS F4-01 行

## 下游消费说明

- F4-02 `useMetrics` 调用六模板函数
