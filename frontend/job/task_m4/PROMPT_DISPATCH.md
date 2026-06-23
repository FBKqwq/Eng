# F4 任务分发 Prompt 手册

> 建议每个执行 Agent 附加 skill：`/elk-frontend-agent`
> 任务详情：`task_m4/F4-xx-*.md` | 进度真相源：`task_m4/STATUS.md`
> 强制基线：`location/frontend/前端开发总体规划.md` §3.1、§3.2、§3.7、§7 F4

---

## 零、执行顺序与可并行任务

```text
阶段 A
└── F4-01  api/metrics.js

阶段 B
└── F4-02  composables/useMetrics.js

阶段 C（可并行，3 Agent）
├── F4-04  utils/logTypeMeta.js（chartTemplates）
├── F4-05  dashboard/HealthOverview.vue
└── F4-06  TrafficErrorPanel + LatencyPanel

阶段 D
└── F4-03  monitor/ChartBand.vue

阶段 E
└── F4-07  dashboard 装配 + AlertDigest + LatestReportCard

阶段 F
└── F4-08  funnel 组件 + view

阶段 G（最后）
└── F4-09  frontend/DEV.md
```

### 速查表

| 任务 | 文档 | 唯一负责 | 前置 |
| --- | --- | --- | --- |
| F4-01 | F4-01-metrics_api.md | `api/metrics.js` | F1-03 |
| F4-02 | F4-02-use_metrics.md | `composables/useMetrics.js` | F4-01 |
| F4-03 | F4-03-chart_band.md | `monitor/ChartBand.vue` | F4-02,04 |
| F4-04 | F4-04-log_type_charts.md | `logTypeMeta` chartTemplates | F2-05 |
| F4-05 | F4-05-health_overview.md | `HealthOverview.vue` | F4-02 |
| F4-06 | F4-06-traffic_latency_panels.md | Traffic+Latency Panel | F4-02 |
| F4-07 | F4-07-dashboard_assembly.md | dashboard 三文件 | F4-05,06 |
| F4-08 | F4-08-funnel_page.md | funnel 三文件 | F4-02 |
| F4-09 | F4-09-dev_docs.md | `frontend/DEV.md` | F4-01~08 |

---

## 一、编排 Agent Prompt

```markdown
你是 ELK 前端 F4 编排 Agent。阅读 task_m4/PROMPT_DISPATCH.md、README.md、STATUS.md 与总体规划 §7 F4。
F4-09 仅在 F4-01~08 完成后派发。不要自己写业务代码。提醒执行 Agent 更新 STATUS。
```

---

## 二、完成汇报模板

```markdown
## F4 任务完成汇报 — {TASK_ID}
### 修改文件
### 实现摘要（3~5 条）
### 验收结果（AC 表）
### 自测（npm run build）
### 阻塞与遗留
### STATUS 已更新
```

---

## 三、各任务派发 Prompt

### F4-01 metrics_api

```markdown
/elk-frontend-agent
任务：**F4-01**  (作为会话窗口名称)| 文档：`task_m4/F4-01-metrics_api.md`
唯一修改：`src/api/metrics.js`
要点：六模板函数；USE_MOCK=false 默认；mock 形态对齐 schema
```

### F4-02 use_metrics

```markdown
/elk-frontend-agent
任务：**F4-02**  (作为会话窗口名称)| 文档：`task_m4/F4-02-use_metrics.md`
依赖：F4-01
唯一修改：`src/composables/useMetrics.js`
要点：template 枚举；inject useTimeRange；isMock 角标支持
```

### F4-03 chart_band

```markdown
/elk-frontend-agent
任务：**F4-03**  (作为会话窗口名称)| 文档：`task_m4/F4-03-chart_band.md`
依赖：F4-02、F4-04
唯一修改：`src/components/monitor/ChartBand.vue`
要点：chartTemplates 驱动；替换 F2 占位
```

### F4-04 log_type_charts

```markdown
/elk-frontend-agent
任务：**F4-04**  (作为会话窗口名称)| 文档：`task_m4/F4-04-log_type_charts.md`
唯一修改：`src/utils/logTypeMeta.js`（仅 chartTemplates）
要点：7 类各 2~3 模板；对齐 §3.2 表
```

### F4-05 health_overview

```markdown
/elk-frontend-agent
任务：**F4-05**  (作为会话窗口名称)| 文档：`task_m4/F4-05-health_overview.md`
依赖：F4-02
唯一修改：`src/components/dashboard/HealthOverview.vue`
要点：Gauge + 5 StatCard；环比箭头先隐藏
```

### F4-06 traffic_latency_panels

```markdown
/elk-frontend-agent
任务：**F4-06**  (作为会话窗口名称)| 文档：`task_m4/F4-06-traffic_latency_panels.md`
依赖：F4-02
唯一修改：`TrafficErrorPanel.vue` + `LatencyPanel.vue`
```

### F4-07 dashboard_assembly

```markdown
/elk-frontend-agent
任务：**F4-07**  (作为会话窗口名称)| 文档：`task_m4/F4-07-dashboard_assembly.md`
依赖：F4-05、F4-06
唯一修改：`dashboard/index.vue` + `AlertDigest.vue` + `LatestReportCard.vue`
要点：预警/报告 mock 路径 + 演示角标
```

### F4-08 funnel_page

```markdown
/elk-frontend-agent
任务：**F4-08**  (作为会话窗口名称)| 文档：`task_m4/F4-08-funnel_page.md`
依赖：F4-02
唯一修改：funnel 组件×2 + `views/analysis/funnel.vue`
```

### F4-09 dev_docs（最后）

```markdown
/elk-frontend-agent
任务：**F4-09**  (作为会话窗口名称)| 文档：`task_m4/F4-09-dev_docs.md`
依赖：F4-01~08 全部完成
唯一修改：`frontend/DEV.md`
```

---

## 四、推荐派发时间线

| 时间点 | 派发 | Agent 数 |
| --- | --- | --- |
| T0 | F4-01 | 1 |
| T1 | F4-02 | 1 |
| T2 | F4-04 + F4-05 + F4-06 | 3 |
| T3 | F4-03 | 1 |
| T4 | F4-07 + F4-08 | 2 |
| T5 | F4-09 | 1 |
