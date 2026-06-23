# F7 任务分发 Prompt 手册

> 建议每个执行 Agent 附加 skill：`/elk-frontend-agent`
> 任务详情：`task_m7/F7-xx-*.md` | 进度真相源：`task_m7/STATUS.md`
> 强制基线：总体规划 §8、skill §9.7

---

## 零、执行顺序与可并行任务

```text
阶段 A（可并行）
├── F7-03  .env.example + kibanaLinks.js
└── F7-04  styles + BaseChart 动效

阶段 B
└── F7-01  RelationInsightCard.vue

阶段 C
└── F7-02  StatCard + funnel 对比 tab

阶段 D（可选）
└── F7-05  ParticleBackdrop + 白名单三页挂载

阶段 E（最后）
└── F7-06  frontend/DEV.md
```

### 速查表

| 任务 | 文档 | 唯一负责 | 前置 |
| --- | --- | --- | --- |
| F7-01 | F7-01-relation_insight.md | `RelationInsightCard.vue` | F6-04 |
| F7-02 | F7-02-dual_window_compare.md | `StatCard`+`funnel.vue` | F4-05,08 |
| F7-03 | F7-03-kibana_links.md | env+kibanaLinks.js | F3 |
| F7-04 | F7-04-motion_polish.md | styles+BaseChart | F4 |
| F7-05 | F7-05-particle_backdrop.md | ParticleBackdrop+3 views | F4-07,F3-05,F5-06 |
| F7-06 | F7-06-dev_docs.md | `frontend/DEV.md` | F7-01~05 |

---

## 一、编排 Agent Prompt

```markdown
你是 ELK 前端 F7 编排 Agent。F7 为最后里程碑。
F7-05 可选；不达标则跳过。F7-06 最后派发。不要自己写业务代码。
```

---

## 二、完成汇报模板

```markdown
## F7 任务完成汇报 — {TASK_ID}
### 修改文件
### 实现摘要
### 验收结果（AC 或 P 表）
### STATUS 已更新
```

---

## 三、各任务派发 Prompt

### F7-01 relation_insight

```markdown
/elk-frontend-agent
任务：**F7-01**  (作为会话窗口名称)| 文档：`task_m7/F7-01-relation_insight.md`
唯一修改：`RelationInsightCard.vue`
要点：relation_chain 箭头卡+双迷你折线
```

### F7-02 dual_window_compare

```markdown
/elk-frontend-agent
任务：**F7-02**  (作为会话窗口名称)| 文档：`task_m7/F7-02-dual_window_compare.md`
唯一修改：`StatCard.vue` + `views/analysis/funnel.vue`
要点：环比箭头；漏斗对比 tab 未就绪则隐藏
```

### F7-03 kibana_links

```markdown
/elk-frontend-agent
任务：**F7-03**  (作为会话窗口名称)| 文档：`task_m7/F7-03-kibana_links.md`
唯一修改：`.env.example` + `utils/kibanaLinks.js`
```

### F7-04 motion_polish

```markdown
/elk-frontend-agent
任务：**F7-04**  (作为会话窗口名称)| 文档：`task_m7/F7-04-motion_polish.md`
唯一修改：`assets/styles/index.css` + `charts/BaseChart.vue`
要点：reduce-motion；图表过渡 300~500ms
```

### F7-05 particle_backdrop（可选）

```markdown
/elk-frontend-agent
任务：**F7-05**  (作为会话窗口名称)| 文档：`task_m7/F7-05-particle_backdrop.md`
唯一修改：ParticleBackdrop + 白名单三 view 挂载
强制：skill §9.7 P-01~P-07；不达标则不做
```

### F7-06 dev_docs（最后）

```markdown
/elk-frontend-agent
任务：**F7-06**  (作为会话窗口名称)| 文档：`task_m7/F7-06-dev_docs.md`
唯一修改：`frontend/DEV.md`
要点：F1~F7 总览收尾
```

---

## 四、推荐派发时间线

| 时间点 | 派发 | Agent 数 |
| --- | --- | --- |
| T0 | F7-03 + F7-04 | 2 |
| T1 | F7-01 | 1 |
| T2 | F7-02 | 1 |
| T3 | F7-05（可选） | 1 |
| T4 | F7-06 | 1 |
