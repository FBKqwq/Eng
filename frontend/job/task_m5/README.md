# F5 智能线 — 前端 Agent 任务编排说明

> 对应总体规划：`location/frontend/前端开发总体规划.md` §3.3、§3.6、§5、§7（阶段 F5）
> 目标：异常诊断中心全量可视化 + 调用链路追踪页；智能体产出耦合进业务页，禁止对话框。
> 原则：**一个 Agent 只负责一组互不重叠的文件**。

---

## 1. 阶段定位

F5 交付「智能分析可视化」：

- 诊断中心：输入 → 结论仪表 → 证据链 → 建议 + 阶段环。
- 链路追踪：trace_id 检索 + 泳道瀑布图。
- 遵守 §5：数值先于文字、`StageRing` 唯一进度载体、降级角标。

F5 **不做**：报告/预警页（F6）、聚合驾驶舱（F4 已完成部分）。

---

## 2. 任务清单与文件归属

| 任务编号 | 文档 | 唯一负责文件/目录 | 禁止修改 |
| --- | --- | --- | --- |
| F5-01 | [F5-01-diagnosis_api.md](./F5-01-diagnosis_api.md) | `src/api/diagnosis.js` | 其他所有文件 |
| F5-02 | [F5-02-diagnosis_entry.md](./F5-02-diagnosis_entry.md) | `DiagnosisEntryPanel.vue` | 其他所有文件 |
| F5-03 | [F5-03-conclusion_panel.md](./F5-03-conclusion_panel.md) | `ConclusionPanel.vue` | 其他所有文件 |
| F5-04 | [F5-04-evidence_topology.md](./F5-04-evidence_topology.md) | `EvidenceTimeline.vue` + `ServiceTopology.vue` | 其他所有文件 |
| F5-05 | [F5-05-suggestion_stage.md](./F5-05-suggestion_stage.md) | `SuggestionChecklist.vue` + `DiagnosisStageRing.vue` | 其他所有文件 |
| F5-06 | [F5-06-diagnosis_view.md](./F5-06-diagnosis_view.md) | `views/analysis/diagnosis.vue` | 其他所有文件 |
| F5-07 | [F5-07-trace_components.md](./F5-07-trace_components.md) | `TraceSearchBar.vue` + `TraceWaterfall.vue` | 其他所有文件 |
| F5-08 | [F5-08-trace_view.md](./F5-08-trace_view.md) | `views/analysis/trace.vue` | 其他所有文件 |
| F5-09 | [F5-09-dev_docs.md](./F5-09-dev_docs.md) | `frontend/DEV.md` | 业务代码文件 |

**说明**：`StageRing.vue` 本体属 F1-06；F5-05 新增 `DiagnosisStageRing.vue` 薄包装，将 `node_trace` 映射为业务阶段语义，**禁止修改** `common/StageRing.vue`。

---

## 3. 推荐执行顺序

```text
阶段 A
  F5-01 diagnosis.js

阶段 B（可并行）
  F5-02 DiagnosisEntryPanel
  F5-07 TraceSearchBar + TraceWaterfall

阶段 C（可并行）
  F5-03 ConclusionPanel
  F5-04 EvidenceTimeline + ServiceTopology
  F5-05 SuggestionChecklist + DiagnosisStageRing

阶段 D（可并行）
  F5-06 diagnosis.vue
  F5-08 trace.vue

阶段 E
  F5-09 dev_docs
```

---

## 4. 跨任务约定

1. 禁止「智能体」「Agent」「LLM」等调度字眼出现在 UI。
2. 禁止聊天气泡；根因/建议必须版式化卡片。
3. `node_trace` 仅通过 `StageRing`（或 F5-05 包装件）展示业务阶段语义。
4. LLM 降级显示「规则判定」「统计模式」灰色角标。
5. trace 页与 F2 LogTable 跳转 query 对齐：`trace_id`。
6. 全部简体中文；不要 commit（除非负责人要求）。

---

## 5. F5 总体验收

- [ ] 诊断页四区完整；提交异常日志后结论/证据/建议/阶段环可见。
- [ ] 降级态可感知（规则判定角标、LLM 阶段跳过）。
- [ ] 链路追踪页可按 trace_id 展示瀑布图；从监控页带参跳入可用。
- [ ] `npm run build` 通过；DEV.md 更新。

---

## 6. 后端依赖

| 接口 | 状态 | F5 行为 |
| --- | --- | --- |
| `POST /api/v1/diagnosis` | M5 已落地 | 必须接入；`res.data.diagnosis`（**无** `node_trace`） |
| `searchByTraceId` → `POST /logs/search` | M1 已落地；**须 F1-18** | 链路页必须接入；**禁止** `GET /logs/trace/{id}` |
| `GET /analysis/runs/recent`、`POST /analysis/run` | M6 已落地；**须 F1-18** | 阶段环可选；`data.node_trace` |
