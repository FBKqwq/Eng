# F2 监控线 — 前端 Agent 任务编排说明

> 对应总体规划：`location/frontend/前端开发总体规划.md` §3.2、§7（阶段 F2）
> 目标：LogMonitorShell 三段式骨架接入真实日志查询；DynamicFilterBar 动态筛选；LogTable 分页/展开/trace 跳转；7 子页配置驱动可查真实明细。
> 原则：**一个 Agent 只负责一组互不重叠的文件**，避免并行改同一文件。
> 边界：本里程碑只涉及 `location/frontend/`；**图表带仍占位**（真实聚合留 F4）。

---

## 1. 阶段定位

F2 交付「监控页可查真实日志」，不接聚合图表：

- `POST /api/v1/logs/search` 驱动 7 个子页明细表，分页/排序可用。
- `GET /api/v1/logs/fields?log_type=` 驱动动态筛选；未就绪时用 `logTypeMeta` 本地兜底并标注。
- `LogTable` 支持行展开、含 `trace_id` 行跳转 `/analysis/trace?trace_id=`。
- `ChartBand` **保持 F1 占位**，不阻塞 F2 验收。

F2 **不做**：聚合图表（F4）、系统页迁移（F3）、诊断/报告/预警（F5/F6）。

---

## 2. 任务清单与文件归属

| 任务编号 | 文档 | 唯一负责文件/目录 | 禁止修改 |
| --- | --- | --- | --- |
| F2-01 | [F2-01-logs_api.md](./F2-01-logs_api.md) | `src/api/logs.js` | 其他所有文件 |
| F2-02 | [F2-02-use_log_query.md](./F2-02-use_log_query.md) | `src/composables/useLogQuery.js`（新建） | 其他所有文件 |
| F2-03 | [F2-03-log_table.md](./F2-03-log_table.md) | `src/components/common/LogTable.vue` | 其他所有文件 |
| F2-04 | [F2-04-dynamic_filter.md](./F2-04-dynamic_filter.md) | `src/components/monitor/DynamicFilterBar.vue` | 其他所有文件 |
| F2-05 | [F2-05-log_type_meta.md](./F2-05-log_type_meta.md) | `src/utils/logTypeMeta.js` | 其他所有文件 |
| F2-06 | [F2-06-log_monitor_shell.md](./F2-06-log_monitor_shell.md) | `src/components/monitor/LogMonitorShell.vue` | ChartBand.vue、views/ |
| F2-07 | [F2-07-monitor_views.md](./F2-07-monitor_views.md) | `src/views/monitor/*.vue`（7 个子页） | 其他所有文件 |
| F2-08 | [F2-08-dev_docs.md](./F2-08-dev_docs.md) | `frontend/DEV.md` | 业务代码文件 |

---

## 3. 推荐执行顺序

```text
阶段 A（可并行，2 Agent）
  F2-01 logs.js 扩展          ← search/fields 契约对齐
  F2-05 logTypeMeta.js        ← 7 类默认列/筛选项兜底

阶段 B（依赖 A）
  F2-02 useLogQuery.js        ← 统一查询状态（分页/排序/筛选/时间窗）

阶段 C（可并行，2 Agent；依赖 B）
  F2-03 LogTable.vue          ← 真实表格
  F2-04 DynamicFilterBar.vue  ← 动态筛选

阶段 D（串行）
  F2-06 LogMonitorShell.vue   ← 串联筛选+表+查询（ChartBand 仍占位）

阶段 E
  F2-07 monitor 7 views       ← 配置对象微调（通常仅 props 对齐）

阶段 F（全部完成后）
  F2-08 dev_docs
```

---

## 4. 跨任务约定

1. **只改自己负责的文件**；Shell 通过 props/events 与 Filter/Table 通信，不内联表格 DOM。
2. 时间窗统一 `useTimeRange()` inject，变更触发重查。
3. fields 接口失败时 `DynamicFilterBar` 降级本地 meta，UI 标注「字段目录兜底」。
4. `ChartBand.vue` 本阶段**禁止**接入 metrics（归 F4-03）。
5. **API 契约**：必读 [`job/API_CONTRACT.md`](../API_CONTRACT.md)；`searchLogs` 用 `start_time/end_time`；错误 `e.error?.code`。
6. 全部中文使用**简体中文**；除非负责人明确要求，**不要 commit**。

---

## 5. F2 总体验收

- [ ] 7 个 `/monitor/*` 子页可查询真实日志（或 ES 离线时展示结构化错误态，不白屏）。
- [ ] 分页、排序、关键字筛选可用；全局时间窗变更后重查。
- [ ] 动态筛选器渲染 fields 或兜底 meta；未就绪处有明确标注。
- [ ] `LogTable` 行展开、trace_id 跳转链路追踪页可用。
- [ ] 图表带仍为占位，标注 `pending-api metrics`。
- [ ] `npm run build` 通过。
- [ ] `frontend/DEV.md` 反映 F2 落地状态。

---

## 6. 后端依赖声明

| 接口 | 状态 | F2 行为 |
| --- | --- | --- |
| `POST /api/v1/logs/search` | M1 已落地 | 必须接入 |
| `GET /api/v1/logs/fields?log_type=` | M1 已落地 | 优先接入；失败走 logTypeMeta 兜底 |
| `POST /api/v1/logs/aggregate` | M1 已落地 | F2 不接入，ChartBand 占位（F4 接入） |
