# F6 任务分发 Prompt 手册

> 建议每个执行 Agent 附加 skill：`/elk-frontend-agent`
> 任务详情：`task_m6/F6-xx-*.md` | 进度真相源：`task_m6/STATUS.md`
> 强制基线：总体规划 §3.4、§3.5、§7 F6

---

## 零、执行顺序与可并行任务

```text
阶段 A（可并行）
├── F6-01  api/reports.js
└── F6-02  api/alerts.js

阶段 B（可并行）
├── F6-03  reports 三组件
└── F6-05  alerts 三组件

阶段 C（可并行）
├── F6-04  views/analysis/reports.vue
└── F6-06  views/analysis/alerts.vue

阶段 D
└── F6-07  TopBar + AlertDigest + LatestReportCard

阶段 E（最后）
└── F6-08  frontend/DEV.md
```

### 速查表

| 任务 | 文档 | 唯一负责 | 前置 |
| --- | --- | --- | --- |
| F6-01 | F6-01-reports_api.md | `api/reports.js` | F1-03 |
| F6-02 | F6-02-alerts_api.md | `api/alerts.js` | F1-03 |
| F6-03 | F6-03-reports_components.md | reports 三组件 | F6-01 |
| F6-04 | F6-04-reports_view.md | `reports.vue` | F6-03 |
| F6-05 | F6-05-alerts_components.md | alerts 三组件 | F6-02 |
| F6-06 | F6-06-alerts_view.md | `alerts.vue` | F6-05 |
| F6-07 | F6-07-global_alert_wiring.md | TopBar+两摘要卡 | F6-01,02,F4-07 |
| F6-08 | F6-08-dev_docs.md | `frontend/DEV.md` | F6-01~07 |

---

## 一、编排 Agent Prompt

```markdown
你是 ELK 前端 F6 编排 Agent。阅读 task_m6 文档。
F6-07 依赖 API 与 F4-07 摘要组件；F6-08 最后派发。不要自己写业务代码。
```

---

## 二、完成汇报模板

```markdown
## F6 任务完成汇报 — {TASK_ID}
### 修改文件
### 实现摘要
### 验收结果（AC）
### STATUS 已更新
```

---

## 三、各任务派发 Prompt

### F6-01 reports_api

```markdown
/elk-frontend-agent
任务：**F6-01**  (作为会话窗口名称)| 文档：`task_m6/F6-01-reports_api.md`
唯一修改：`src/api/reports.js` + `STATUS.md`
要点：getRecentReports/getReportDetail；USE_MOCK 切换
```

### F6-02 alerts_api

```markdown
/elk-frontend-agent
任务：**F6-02**  (作为会话窗口名称)| 文档：`task_m6/F6-02-alerts_api.md`
唯一修改：`src/api/alerts.js` + `STATUS.md`
要点：getActiveAlerts；acknowledgeAlert
```

### F6-03 reports_components

```markdown
/elk-frontend-agent
任务：**F6-03**  (作为会话窗口名称)| 文档：`task_m6/F6-03-reports_components.md`
唯一修改：ReportTimeline + ReportRiskPanel + ReportSections + `STATUS.md`
```

### F6-04 reports_view

```markdown
/elk-frontend-agent
任务：**F6-04**  (作为会话窗口名称)| 文档：`task_m6/F6-04-reports_view.md`
唯一修改：`views/analysis/reports.vue` + `STATUS.md`
```

### F6-05 alerts_components

```markdown
/elk-frontend-agent
任务：**F6-05**  (作为会话窗口名称)| 文档：`task_m6/F6-05-alerts_components.md`
唯一修改：AlertBoard + AlertTable + AlertDetailDrawer + `STATUS.md`
```

### F6-06 alerts_view

```markdown
/elk-frontend-agent
任务：**F6-06**  (作为会话窗口名称)| 文档：`task_m6/F6-06-alerts_view.md`
唯一修改：`views/analysis/alerts.vue` + `STATUS.md`
```

### F6-07 global_alert_wiring

```markdown
/elk-frontend-agent
任务：**F6-07**  (作为会话窗口名称)| 文档：`task_m6/F6-07-global_alert_wiring.md`
唯一修改：TopBar + AlertDigest + LatestReportCard + `STATUS.md`
要点：USE_MOCK=false；30s 轮询真实角标
```

### F6-08 dev_docs（最后）

```markdown
/elk-frontend-agent
任务：**F6-08**  (作为会话窗口名称)| 文档：`task_m6/F6-08-dev_docs.md`
唯一修改：`frontend/DEV.md` + `STATUS.md`
```

---

## 四、推荐派发时间线

| 时间点 | 派发 | Agent 数 |
| --- | --- | --- |
| T0 | F6-01 + F6-02 | 2 |
| T1 | F6-03 + F6-05 | 2 |
| T2 | F6-04 + F6-06 | 2 |
| T3 | F6-07 | 1 |
| T4 | F6-08 | 1 |
