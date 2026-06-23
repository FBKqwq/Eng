# F3 系统线 — 前端 Agent 任务编排说明

> 对应总体规划：`location/frontend/前端开发总体规划.md` §3.8、§7（阶段 F3）
> 目标：系统运维三页无能力回退——链路图+验证、组件状态卡矩阵、配置快照；迁移旧 `views/system/index.vue` 能力。
> 原则：**一个 Agent 只负责一组互不重叠的文件**。
> 边界：仅 `location/frontend/`；与 F2 可并行（改不同目录）。

---

## 1. 阶段定位

F3 交付「系统运维三页真实可用」：

- `/system/pipeline`：四节点链路图 + `verify_pipeline` 一键验证 + 终端输出。
- `/system/components`：Kafka/ES/Logstash/Kibana/Backend/LLM 状态卡矩阵（含 DEV.md 兜底规则）。
- `/system/config`：只读配置快照 + Kibana 外链（`VITE_KIBANA_URL`）。

F3 **不做**：监控日志（F2）、聚合图表（F4）、诊断/报告（F5/F6）。

---

## 2. 任务清单与文件归属

| 任务编号 | 文档 | 唯一负责文件/目录 | 禁止修改 |
| --- | --- | --- | --- |
| F3-01 | [F3-01-system_api.md](./F3-01-system_api.md) | `src/api/system.js` | 其他所有文件 |
| F3-02 | [F3-02-system_status_utils.md](./F3-02-system_status_utils.md) | `src/utils/systemStatus.js` | 其他所有文件 |
| F3-03 | [F3-03-pipeline_graph.md](./F3-03-pipeline_graph.md) | `src/components/system/PipelineGraph.vue` | 其他所有文件 |
| F3-04 | [F3-04-verify_output.md](./F3-04-verify_output.md) | `src/components/system/VerifyOutputPanel.vue` | 其他所有文件 |
| F3-05 | [F3-05-pipeline_view.md](./F3-05-pipeline_view.md) | `src/views/system/pipeline.vue` | 其他所有文件 |
| F3-06 | [F3-06-status_card.md](./F3-06-status_card.md) | `src/components/common/StatusCard.vue` | 其他所有文件 |
| F3-07 | [F3-07-components_view.md](./F3-07-components_view.md) | `src/views/system/components.vue` | 其他所有文件 |
| F3-08 | [F3-08-config_snapshot.md](./F3-08-config_snapshot.md) | `src/components/system/ConfigSnapshotCard.vue` | 其他所有文件 |
| F3-09 | [F3-09-config_view.md](./F3-09-config_view.md) | `src/views/system/config.vue` | 其他所有文件 |
| F3-10 | [F3-10-dev_docs.md](./F3-10-dev_docs.md) | `frontend/DEV.md` | 业务代码文件 |

**说明**：旧 `views/system/index.vue`、`ServiceStatusCard.vue` 本阶段**不删除**，新页能力对齐后标记废弃；F3-07 可只读参考旧实现。

---

## 3. 推荐执行顺序

```text
阶段 A（可并行）
  F3-01 system.js
  F3-02 systemStatus.js

阶段 B（可并行）
  F3-03 PipelineGraph.vue
  F3-04 VerifyOutputPanel.vue
  F3-06 StatusCard.vue          ← 通用化，供 components 页使用

阶段 C
  F3-05 pipeline.vue            ← 组合 F3-03/04
  F3-08 ConfigSnapshotCard.vue

阶段 D（可并行）
  F3-07 components.vue
  F3-09 config.vue

阶段 E
  F3-10 dev_docs
```

---

## 4. 跨任务约定

1. **只改自己负责的文件**；页面通过 props/events 与子组件通信。
2. system API 为真实接口，不使用 USE_MOCK。
3. 保留旧 `views/system/index.vue`，新三页能力对齐后 DEV.md 标记废弃。
4. `PipelineHealthDot`（F1）行为不得回归。
5. Kibana 入口先读 `VITE_KIBANA_URL`；深链生成留 F7-03。
6. 全部简体中文；除非负责人明确要求，**不要 commit**。

---

## 5. F3 总体验收

- [ ] 链路页可展示四节点状态着色，一键验证有输出（成功/失败结构化展示）。
- [ ] 组件页 6+ 状态卡正确反映 `/system/status`，含 containers/services 兜底与 ES unknown 兜底。
- [ ] 配置页只读展示 kafka/es/llm 等字段；Kibana 按钮在 URL 配置时可用。
- [ ] aside `PipelineHealthDot` 行为与链路页一致（F1 已有，F3 不回归）。
- [ ] `npm run build` 通过；DEV.md 更新。

---

## 6. 后端依赖

| 接口 | 状态 |
| --- | --- |
| `GET /system/status` | 已有 |
| `POST /system/pipeline/verify` | 已有 |
| `GET /health` | 已有 |
