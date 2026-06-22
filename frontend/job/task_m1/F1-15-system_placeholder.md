# F1-15：系统运维 3 页占位 system_placeholder

## Agent 角色

系统运维页骨架专项 Agent — **仅搭建链路/组件/配置 3 页骨架与占位**。

## 唯一负责文件/目录

```
src/views/system/pipeline.vue
src/views/system/components.vue
src/views/system/config.vue
src/components/system/PipelineGraph.vue
src/components/system/VerifyOutputPanel.vue
src/components/system/ConfigSnapshotCard.vue
```

## 禁止修改

- `views/system/index.vue`（旧系统页，保留，能力迁移归 F3）
- `components/system/ServiceStatusCard.vue`（旧件，保留）
- `utils/systemStatus.js`、`api/system.js`（只 import）
- `components/common/`、其他页面目录、`router/index.js`

## 前置依赖

- F1-06 common（`EmptyState`/`StatusCard`）

## 开发要求

### 1. 各页编排（对齐总体规划 §3.8）

| 页面 | 组件占位 |
| --- | --- |
| pipeline | `PipelineGraph`（四节点链路图占位）+ `VerifyOutputPanel`（验证输出占位，`pending-api="POST /system/pipeline/verify"`） |
| components | 6 张 `StatusCard`（Backend/Kafka/ES/Logstash/Kibana/LLM）占位 + 迁移说明 |
| config | `ConfigSnapshotCard`（Kafka/ES/索引/LLM 只读快照占位，`pending-api="GET /system/status"`） |

### 2. 约束

- **F1 仅占位**；现有 `views/system/index.vue` 的真实能力（状态卡矩阵、全链路验证、兜底规则）**迁移留待 F3**，本任务不删除旧页。
- 不直接 `axios`/`fetch`。
- 简体中文文案。

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 3 页可达 | `/system/{pipeline,components,config}` 渲染不报错 |
| AC-02 | 分区 | 按 §3.8 编排占位 |
| AC-03 | 不回退 | 旧 `views/system/index.vue` 保留未删 |

## 完成定义（DoD）

- [ ] 仅修改 system 新视图与新组件
- [ ] 旧系统页保留
- [ ] 不修改 DEV.md

## 下游消费说明（供其他 Agent 只读）

- F1-16 router 注册 3 个 `/system/*`，`/temp/developer` 复用 components 视图
- F3 将旧系统页能力迁入本三页
