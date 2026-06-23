# 前端任务 API 契约审计报告

> 审计时间：2026-06-23  
> 依据：`/elk-frontend-agent` §三 + `backend/app/api/DEV.md` §4.2 + 现有 `src/api/*` 代码  
> 范围：`location/frontend/job/task_m1` ~ `task_m7` 全部 67+ 项任务文档

---

## 1. 审计结论摘要

| 级别 | 数量 | 说明 |
| --- | ---: | --- |
| 🔴 严重偏差 | 5 | 路径不存在或 mock 形态与契约不符，阻塞真实对接 |
| 🟡 文档过时 | 12+ | 任务文档未写信封解包、字段名或数据源 |
| 🟢 已对齐 | — | `request.js` 已实现信封解包；`system.js` 路径基本正确 |

**处置**：已新增 [`API_CONTRACT.md`](./API_CONTRACT.md) 作为全阶段基线；已新增 **F1-18** 契约回补任务；已批量修订 F1~F7 相关任务文档（见 §3）。**2026-06-23 二轮**：对齐 `前端开发总体规划.md` §6/§7、F2/F4/F5 STATUS、F1-10/F3-02/F1-13 等残留偏差；明确 **F1-18 代码未落地** 为 F2~F6 派发阻塞项。

---

## 2. 代码现状 vs 契约（`src/api/`）

| 文件 | 问题 | 契约正确做法 | 归口任务 |
| --- | --- | --- | --- |
| `request.js` | ✅ 已解包 `{ok,data,error}` | 保持；wrapper/页面不再读 `ok` | — |
| `logs.js` | ❌ `getLogTrace` → `/logs/trace/{id}` **不存在**；缺 `aggregateLogs` | `searchLogs({trace_id})`；`POST /logs/aggregate` | F1-18、F2-01 |
| `metrics.js` | ❌ `POST /metrics/*` **不存在**；mock 含 `series/total` 非契约字段 | 六模板封装 → `aggregateLogs` | F1-18、F4-01 |
| `alerts.js` | ❌ mock `data: []` 应为 `{ items, total }` | 见 API_CONTRACT §5 | F1-18、F6-02 |
| `reports.js` | ❌ mock `data: []` 应为 `{ items, total, limit }` | 见 API_CONTRACT §5 | F1-18、F6-01 |
| `diagnosis.js` | ⚠️ 仅一行，无 mock/字段注释 | 对齐 `DiagnosisData` 结构 | F5-01 |
| `system.js` | ✅ 基本正确 | F3 补充 `getSystemContainers` 可选 | F3-01 |
| `analysis.js` | ❌ **缺失** | 新建 `/analysis/runs/recent`、`/analysis/run` | F1-18、F5-01 |

### 页面层连带问题

| 位置 | 问题 | 修复任务 |
| --- | --- | --- |
| `TopBar.vue` | 角标兼容 `Array.isArray(data)`，未优先 `data.total` | F6-07 |
| `PipelineHealthDot.vue` | 读 `s.overall`/`pipeline_healthy`，与 status 契约字段可能不一致 | F3-02 |

---

## 3. 各阶段任务文档修订清单

### F1（task_m1）

| 任务 | 修订内容 |
| --- | --- |
| **F1-18（新增）** | API 契约回补：`request` 验收项 + 7 文件 mock/路径修正 + 新建 `analysis.js` |
| F1-03 | 重写为引用 API_CONTRACT；标注 F1 追溯完成但需 F1-18 复审 |
| F1-09 | 角标改为 `data.total`；`catch` 读 `e.error?.code` |
| README / STATUS / PROMPT_DISPATCH | 登记 F1-18；F1-03 备注「待 F1-18 契约复审」 |

### F2（task_m2）

| 任务 | 修订内容 |
| --- | --- |
| F2-01 | `start_time/end_time` 替代 `time_range`；`catalog` 结构；`searchByTraceId`；必读 API_CONTRACT §4.2 |
| F2-02 | 错误处理 `e.error?.code`；UTC 时间格式化 |
| F2-04 | `catalog.filter_fields` 驱动控件 |

### F3（task_m3）

| 任务 | 修订内容 |
| --- | --- |
| F3-01 | 补充 `getSystemContainers`；verify 响应字段引用契约 |
| F3-02 | 去除 `available` 总开关依赖；按嵌套 `kafka.available` 等判断 |

### F4（task_m4）

| 任务 | 修订内容 |
| --- | --- |
| F4-01 | **删除** `/metrics/*`；改为六模板 → `aggregateLogs` |
| F4-02/03 | `buckets` 数据结构；mock 形态对齐 |
| README | 后端依赖改为 `POST /logs/aggregate`（M1 已落地） |

### F5（task_m5）

| 任务 | 修订内容 |
| --- | --- |
| F5-01 | 拆分 `diagnosis.js` + `analysis.js`；诊断响应无 `node_trace` 说明 |
| F5-05 | `node_trace` 来源：`analysis/run` 或 `reports/{id}` |
| F5-07/08 | 删除 `getLogTrace`；改 `searchByTraceId` |

### F6（task_m6）

| 任务 | 修订内容 |
| --- | --- |
| F6-01/02 | mock `items+total`；`USE_MOCK=false`（M4/M5 已就绪） |
| F6-07 | TopBar `data.total`；信封已解包说明 |

### F7（task_m7）

| 任务 | 修订内容 |
| --- | --- |
| F7-01 | relation 数据字段对齐 `report` 详情结构 |
| F7-03 | Kibana 外链不走 ES API |

### 全局

| 文件 | 修订内容 |
| --- | --- |
| `job/README.md` | 链接 API_CONTRACT + API_AUDIT |
| 各 README §跨任务约定 | 增加「API 任务必读 API_CONTRACT.md」 |

---

## 4. 推荐执行顺序（API 专项）

```text
F1-18（契约回补，优先于 F2/F4/F6 真实对接）
  ↓
F2-01（logs 扩展）∥ F4-01（metrics→aggregate）∥ F6-01/02（reports/alerts 关 mock）
  ↓
各页面接入任务按原里程碑顺序
```

---

## 5. 与总体规划的差异说明

| 总体规划 §6 原文 | 契约现实 | 任务文档处置 |
| --- | --- | --- |
| `metrics.js` 六模板独立接口 | 统一 `POST /logs/aggregate` | F4-01 + **总体规划 §6 已回写** |
| `GET /logs/trace/{id}` | 不存在 | 全任务改为 `searchByTraceId`；**总体规划 §6 已回写** |
| reports/alerts「待后端 P2」 | M4/M5 已真实对接 | F6 默认 `USE_MOCK=false`；**总体规划 §6 已标注后端/前端分层状态** |
