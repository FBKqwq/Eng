# F2 任务分发 Prompt 手册

> 建议每个执行 Agent 附加 skill：`/elk-frontend-agent`
> 任务详情：`task_m2/F2-xx-*.md` | 进度真相源：`task_m2/STATUS.md`
> 强制基线：`location/frontend/前端开发总体规划.md` §3.2、§7 F2

---

## 零、执行顺序与可并行任务

```text
阶段 A（可并行）
├── F2-01  api/logs.js
└── F2-05  utils/logTypeMeta.js

阶段 B
└── F2-02  composables/useLogQuery.js        ← 依赖 F2-01

阶段 C（可并行）
├── F2-03  common/LogTable.vue               ← 依赖 F2-02
└── F2-04  monitor/DynamicFilterBar.vue      ← 依赖 F2-01、F2-05

阶段 D
└── F2-06  monitor/LogMonitorShell.vue     ← 依赖 F2-02/03/04

阶段 E
└── F2-07  views/monitor/*.vue（7）          ← 依赖 F2-05/06

阶段 F（最后）
└── F2-08  frontend/DEV.md
```

### 速查表

| 任务 | 文档 | 唯一负责 | 前置 |
| --- | --- | --- | --- |
| F2-01 | F2-01-logs_api.md | `api/logs.js` | F1-03 |
| F2-02 | F2-02-use_log_query.md | `composables/useLogQuery.js` | F2-01 |
| F2-03 | F2-03-log_table.md | `common/LogTable.vue` | F2-02 |
| F2-04 | F2-04-dynamic_filter.md | `monitor/DynamicFilterBar.vue` | F2-01,F2-05 |
| F2-05 | F2-05-log_type_meta.md | `utils/logTypeMeta.js` | F1-04 |
| F2-06 | F2-06-log_monitor_shell.md | `monitor/LogMonitorShell.vue` | F2-02~04 |
| F2-07 | F2-07-monitor_views.md | `views/monitor/*.vue` | F2-05,06 |
| F2-08 | F2-08-dev_docs.md | `frontend/DEV.md` | F2-01~07 |

---

## 一、编排 Agent Prompt

```markdown
你是 ELK 前端 F2 编排 Agent。阅读 task_m2/PROMPT_DISPATCH.md、README.md、STATUS.md 与前端总体规划 §7 F2。
根据 STATUS 判断可派发任务；F2-08 仅在 F2-01~07 完成后派发。不要自己写业务代码。
派发后提醒执行 Agent 更新 STATUS 本人任务行。
```

---

## 二、完成汇报模板

```markdown
## F2 任务完成汇报 — {TASK_ID}
### 修改文件
### 实现摘要（3~5 条）
### 验收结果（AC 表）
### 自测（npm run build）
### 阻塞与遗留
### STATUS 已更新
```

---

## 三、各任务派发 Prompt（统一头部：/elk-frontend-agent；只改负责文件；不 commit）

### F2-01 logs_api（阶段 A）

```markdown
/elk-frontend-agent
任务：**F2-01** (作为会话窗口名称) | 文档：`task_m2/F2-01-logs_api.md`
STATUS：开工前 F1-03 已完成；改 F2-01 行为 `进行中`
唯一修改：`src/api/logs.js`
要点：完善 searchLogs 分页/排序契约；getLogFields(logType)
验收：AC-01~04；更新 STATUS F2-01 行
```

### F2-02 use_log_query（阶段 B）

```markdown
/elk-frontend-agent
任务：**F2-02** (作为会话窗口名称) | 文档：`task_m2/F2-02-use_log_query.md`
依赖：F2-01 已完成
唯一修改：`src/composables/useLogQuery.js`（新建）
要点：统一查询状态；inject useTimeRange；range 变更自动 fetch
```

### F2-03 log_table（阶段 C）

```markdown
/elk-frontend-agent
任务：**F2-03**  (作为会话窗口名称)| 文档：`task_m2/F2-03-log_table.md`
依赖：F2-02 已完成
唯一修改：`src/components/common/LogTable.vue`
要点：分页/排序/行展开/trace 跳转事件；不调 api
```

### F2-04 dynamic_filter（阶段 C，可与 F2-03 并行）

```markdown
/elk-frontend-agent
任务：**F2-04** (作为会话窗口名称) | 文档：`task_m2/F2-04-dynamic_filter.md`
依赖：F2-01、F2-05 已完成
唯一修改：`src/components/monitor/DynamicFilterBar.vue`
要点：getLogFields 动态渲染；失败走 logTypeMeta 兜底标注
```

### F2-05 log_type_meta（阶段 A，可与 F2-01 并行）

```markdown
/elk-frontend-agent
任务：**F2-05** (作为会话窗口名称) | 文档：`task_m2/F2-05-log_type_meta.md`
唯一修改：`src/utils/logTypeMeta.js`
要点：7 类 defaultColumns/fallbackFilters/chartTemplates 预留
```

### F2-06 log_monitor_shell（阶段 D）

```markdown
/elk-frontend-agent
任务：**F2-06** (作为会话窗口名称) | 文档：`task_m2/F2-06-log_monitor_shell.md`
依赖：F2-02/03/04 已完成
唯一修改：`src/components/monitor/LogMonitorShell.vue`
禁止修改 ChartBand.vue
要点：串联 Filter+Table+useLogQuery；ChartBand 仍占位
```

### F2-07 monitor_views（阶段 E）

```markdown
/elk-frontend-agent
任务：**F2-07** (作为会话窗口名称) | 文档：`task_m2/F2-07-monitor_views.md`
依赖：F2-05/06 已完成
唯一修改：`src/views/monitor/*.vue`（7 个）
要点：配置驱动 Shell，禁止复制逻辑
```

### F2-08 dev_docs（阶段 F，必须最后）

```markdown
/elk-frontend-agent
任务：**F2-08** (作为会话窗口名称) | 文档：`task_m2/F2-08-dev_docs.md`
依赖：F2-01~07 全部完成
唯一修改：`frontend/DEV.md`
要点：监控线状态表 + F2 开发日志
```

---

## 四、推荐派发时间线

| 时间点 | 派发 | Agent 数 |
| --- | --- | --- |
| T0 | F2-01 + F2-05 | 2 |
| T1 | F2-02 | 1 |
| T2 | F2-03 + F2-04 | 2 |
| T3 | F2-06 | 1 |
| T4 | F2-07 | 1 |
| T5 | F2-08 | 1 |
