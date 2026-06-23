# F3 任务分发 Prompt 手册

> 建议每个执行 Agent 附加 skill：`/elk-frontend-agent`
> 任务详情：`task_m3/F3-xx-*.md` | 进度真相源：`task_m3/STATUS.md`
> 强制基线：`location/frontend/前端开发总体规划.md` §3.8、§7 F3

---

## 零、执行顺序与可并行任务

```text
阶段 A（可并行）
├── F3-01  api/system.js
├── F3-02  utils/systemStatus.js
└── F3-06  common/StatusCard.vue        ← 仅依赖 F1-06

阶段 B（可并行）
├── F3-03  system/PipelineGraph.vue     ← 依赖 F3-02
└── F3-04  system/VerifyOutputPanel.vue ← 依赖 F3-01 契约

阶段 C
├── F3-05  views/system/pipeline.vue    ← 依赖 F3-03/04
└── F3-08  system/ConfigSnapshotCard.vue

阶段 D（可并行）
├── F3-07  views/system/components.vue  ← 依赖 F3-01/02/06
└── F3-09  views/system/config.vue      ← 依赖 F3-08

阶段 E（最后）
└── F3-10  frontend/DEV.md
```

### 速查表

| 任务 | 文档 | 唯一负责 | 前置 |
| --- | --- | --- | --- |
| F3-01 | F3-01-system_api.md | `api/system.js` | F1-03 |
| F3-02 | F3-02-system_status_utils.md | `utils/systemStatus.js` | F1 |
| F3-03 | F3-03-pipeline_graph.md | `system/PipelineGraph.vue` | F3-02 |
| F3-04 | F3-04-verify_output.md | `system/VerifyOutputPanel.vue` | F3-01 |
| F3-05 | F3-05-pipeline_view.md | `views/system/pipeline.vue` | F3-03,04 |
| F3-06 | F3-06-status_card.md | `common/StatusCard.vue` | F1-06 |
| F3-07 | F3-07-components_view.md | `views/system/components.vue` | F3-01,02,06 |
| F3-08 | F3-08-config_snapshot.md | `system/ConfigSnapshotCard.vue` | F3-01 |
| F3-09 | F3-09-config_view.md | `views/system/config.vue` | F3-08 |
| F3-10 | F3-10-dev_docs.md | `frontend/DEV.md` | F3-01~09 |

---

## 一、编排 Agent Prompt

```markdown
你是 ELK 前端 F3 编排 Agent。阅读 task_m3/PROMPT_DISPATCH.md、README.md、STATUS.md 与前端总体规划 §7 F3。
根据 STATUS 判断可派发任务；F3-10 仅在 F3-01~09 完成后派发。不要自己写业务代码。
派发后提醒执行 Agent 更新 STATUS 本人任务行。F3 与 F2 可并行（不同目录）。
```

---

## 二、完成汇报模板

```markdown
## F3 任务完成汇报 — {TASK_ID}
### 修改文件
### 实现摘要（3~5 条）
### 验收结果（AC 表）
### 自测（npm run build）
### 阻塞与遗留
### STATUS 已更新
```

---

## 三、各任务派发 Prompt（统一头部：/elk-frontend-agent；只改负责文件；不 commit）

### F3-01 system_api（阶段 A）

```markdown
/elk-frontend-agent
任务：**F3-01**  (作为会话窗口名称)| 文档：`task_m3/F3-01-system_api.md`
STATUS：开工前 F1-03 已完成；改 F3-01 行为 `进行中`
唯一修改：`src/api/system.js`
要点：getSystemStatus、verifyPipeline(workers)、保留 getHealth
验收：AC-01~04；更新 STATUS F3-01 行
```

### F3-02 system_status_utils（阶段 A）

```markdown
/elk-frontend-agent
任务：**F3-02**  (作为会话窗口名称)| 文档：`task_m3/F3-02-system_status_utils.md`
唯一修改：`src/utils/systemStatus.js`
要点：六组件归一化；containers/services 兜底；getPipelineNodes 四节点
```

### F3-03 pipeline_graph（阶段 B）

```markdown
/elk-frontend-agent
任务：**F3-03**  (作为会话窗口名称)| 文档：`task_m3/F3-03-pipeline_graph.md`
依赖：F3-02 已完成
唯一修改：`src/components/system/PipelineGraph.vue`
要点：四节点横向链路图；状态着色；纯 props
```

### F3-04 verify_output（阶段 B）

```markdown
/elk-frontend-agent
任务：**F3-04**  (作为会话窗口名称)| 文档：`task_m3/F3-04-verify_output.md`
依赖：F3-01 已完成
唯一修改：`src/components/system/VerifyOutputPanel.vue`
要点：workers 输入；emit verify；等宽输出区；组件内不调 api
```

### F3-05 pipeline_view（阶段 C）

```markdown
/elk-frontend-agent
任务：**F3-05**  (作为会话窗口名称)| 文档：`task_m3/F3-05-pipeline_view.md`
依赖：F3-03、F3-04 已完成
唯一修改：`src/views/system/pipeline.vue`
要点：status + verify 编排；组合 Graph + OutputPanel
```

### F3-06 status_card（阶段 A，可与 F3-01/02 并行）

```markdown
/elk-frontend-agent
任务：**F3-06**  (作为会话窗口名称)| 文档：`task_m3/F3-06-status_card.md`
唯一修改：`src/components/common/StatusCard.vue`
要点：通用化状态卡；覆盖旧 ServiceStatusCard 能力
```

### F3-07 components_view（阶段 D）

```markdown
/elk-frontend-agent
任务：**F3-07**  (作为会话窗口名称)| 文档：`task_m3/F3-07-components_view.md`
依赖：F3-01、F3-02、F3-06 已完成
唯一修改：`src/views/system/components.vue`
要点：六卡矩阵；DEV 兜底规则；迁移旧系统页能力
```

### F3-08 config_snapshot（阶段 C）

```markdown
/elk-frontend-agent
任务：**F3-08**  (作为会话窗口名称)| 文档：`task_m3/F3-08-config_snapshot.md`
依赖：F3-01 已完成
唯一修改：`src/components/system/ConfigSnapshotCard.vue`
要点：分组只读键值；LLM 脱敏；Kibana 按钮 props
```

### F3-09 config_view（阶段 D）

```markdown
/elk-frontend-agent
任务：**F3-09**  (作为会话窗口名称)| 文档：`task_m3/F3-09-config_view.md`
依赖：F3-08 已完成
唯一修改：`src/views/system/config.vue`
要点：status → groups 映射；VITE_KIBANA_URL
```

### F3-10 dev_docs（阶段 E，必须最后）

```markdown
/elk-frontend-agent
任务：**F3-10**  (作为会话窗口名称)| 文档：`task_m3/F3-10-dev_docs.md`
依赖：F3-01~09 全部完成
唯一修改：`frontend/DEV.md`
要点：系统线状态表 + 旧页迁移说明 + F3 开发日志
```

---

## 四、推荐派发时间线

| 时间点 | 派发 | Agent 数 |
| --- | --- | --- |
| T0 | F3-01 + F3-02 + F3-06 | 3 |
| T1 | F3-03 + F3-04 + F3-08 | 3 |
| T2 | F3-05 + F3-07 | 2 |
| T3 | F3-09 | 1 |
| T4 | F3-10 | 1 |
