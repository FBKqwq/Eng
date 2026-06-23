# F5 任务分发 Prompt 手册

> 建议每个执行 Agent 附加 skill：`/elk-frontend-agent`
> 任务详情：`task_m5/F5-xx-*.md` | 进度真相源：`task_m5/STATUS.md`
> 强制基线：总体规划 §3.3、§3.6、§5、§7 F5

---

## 零、执行顺序与可并行任务

```text
阶段 A
└── F5-01  api/diagnosis.js

阶段 B（可并行）
├── F5-02  DiagnosisEntryPanel.vue
└── F5-07  TraceSearchBar + TraceWaterfall

阶段 C（可并行）
├── F5-03  ConclusionPanel.vue
├── F5-04  EvidenceTimeline + ServiceTopology
└── F5-05  SuggestionChecklist + DiagnosisStageRing

阶段 D（可并行）
├── F5-06  views/analysis/diagnosis.vue
└── F5-08  views/analysis/trace.vue

阶段 E（最后）
└── F5-09  frontend/DEV.md
```

### 速查表

| 任务 | 文档 | 唯一负责 | 前置 |
| --- | --- | --- | --- |
| F5-01 | F5-01-diagnosis_api.md | `api/diagnosis.js` | F1-03 |
| F5-02 | F5-02-diagnosis_entry.md | `DiagnosisEntryPanel.vue` | F5-01 |
| F5-03 | F5-03-conclusion_panel.md | `ConclusionPanel.vue` | F5-01 |
| F5-04 | F5-04-evidence_topology.md | Evidence+Topology | F5-01 |
| F5-05 | F5-05-suggestion_stage.md | Checklist+StageRing包装 | F5-01,F1-06 |
| F5-06 | F5-06-diagnosis_view.md | `diagnosis.vue` | F5-02~05 |
| F5-07 | F5-07-trace_components.md | Trace 两组件 | F1-03 |
| F5-08 | F5-08-trace_view.md | `trace.vue` | F5-07 |
| F5-09 | F5-09-dev_docs.md | `frontend/DEV.md` | F5-01~08 |

---

## 一、编排 Agent Prompt

```markdown
你是 ELK 前端 F5 编排 Agent。阅读 task_m5 文档与总体规划 §5。
F5-09 最后派发。遵守禁止对话框/禁止独立智能体页。不要自己写业务代码。
```

---

## 二、完成汇报模板

```markdown
## F5 任务完成汇报 — {TASK_ID}
### 修改文件
### 实现摘要
### 验收结果（AC）
### 自测（npm run build）
### STATUS 已更新
```

---

## 三、各任务派发 Prompt

### F5-01 diagnosis_api

```markdown
/elk-frontend-agent
任务：**F5-01**  (作为会话窗口名称)| 文档：`task_m5/F5-01-diagnosis_api.md`
唯一修改：`src/api/diagnosis.js`、`src/api/analysis.js`
要点：submitDiagnosis（`data.diagnosis`，无 node_trace）；analysis 两函数 + 长超时；必读 API_CONTRACT §4.3/§4.5
```

### F5-02 diagnosis_entry

```markdown
/elk-frontend-agent
任务：**F5-02**  (作为会话窗口名称)| 文档：`task_m5/F5-02-diagnosis_entry.md`
依赖：F5-01
唯一修改：`DiagnosisEntryPanel.vue`
```

### F5-03 conclusion_panel

```markdown
/elk-frontend-agent
任务：**F5-03**  (作为会话窗口名称)| 文档：`task_m5/F5-03-conclusion_panel.md`
唯一修改：`ConclusionPanel.vue`
要点：仪表先于文字；禁止聊天气泡
```

### F5-04 evidence_topology

```markdown
/elk-frontend-agent
任务：**F5-04**  (作为会话窗口名称)| 文档：`task_m5/F5-04-evidence_topology.md`
唯一修改：`EvidenceTimeline.vue` + `ServiceTopology.vue`
```

### F5-05 suggestion_stage

```markdown
/elk-frontend-agent
任务：**F5-05**  (作为会话窗口名称)| 文档：`task_m5/F5-05-suggestion_stage.md`
唯一修改：`SuggestionChecklist.vue` + `DiagnosisStageRing.vue`
禁止修改：`common/StageRing.vue`
```

### F5-06 diagnosis_view

```markdown
/elk-frontend-agent
任务：**F5-06**  (作为会话窗口名称)| 文档：`task_m5/F5-06-diagnosis_view.md`
依赖：F5-02~05
唯一修改：`views/analysis/diagnosis.vue`
```

### F5-07 trace_components

```markdown
/elk-frontend-agent
任务：**F5-07**  (作为会话窗口名称)| 文档：`task_m5/F5-07-trace_components.md`
唯一修改：`TraceSearchBar.vue` + `TraceWaterfall.vue`
```

### F5-08 trace_view

```markdown
/elk-frontend-agent
任务：**F5-08**  (作为会话窗口名称)| 文档：`task_m5/F5-08-trace_view.md`
依赖：F5-07
唯一修改：`views/analysis/trace.vue`
```

### F5-09 dev_docs（最后）

```markdown
/elk-frontend-agent
任务：**F5-09**  (作为会话窗口名称)| 文档：`task_m5/F5-09-dev_docs.md`
唯一修改：`frontend/DEV.md`
```

---

## 四、推荐派发时间线

| 时间点 | 派发 | Agent 数 |
| --- | --- | --- |
| T0 | F5-01 | 1 |
| T1 | F5-02 + F5-07 | 2 |
| T2 | F5-03 + F5-04 + F5-05 | 3 |
| T3 | F5-06 + F5-08 | 2 |
| T4 | F5-09 | 1 |
