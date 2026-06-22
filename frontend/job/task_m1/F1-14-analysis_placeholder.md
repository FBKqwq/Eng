# F1-14：智能分析 5 页占位 analysis_placeholder

## Agent 角色

智能分析页骨架专项 Agent — **仅搭建诊断/报告/预警/链路/漏斗 5 页骨架与占位**。

## 唯一负责文件/目录

```
src/views/analysis/diagnosis.vue
src/views/analysis/reports.vue
src/views/analysis/alerts.vue
src/views/analysis/trace.vue
src/views/analysis/funnel.vue
src/components/analysis-diagnosis/*
src/components/analysis-reports/*
src/components/analysis-alerts/*
src/components/analysis-trace/*
src/components/analysis-funnel/*
```

## 禁止修改

- `components/common/`、其他页面目录、`router/index.js`、`layout/`

## 前置依赖

- F1-05 charts、F1-06 common（`EmptyState`/`GaugeChart`/`TimeAxis`/`StageRing`/`StatCard`）

## 开发要求

### 1. 各页编排（对齐总体规划 §3.3~§3.7）

| 页面 | 组件占位 |
| --- | --- |
| diagnosis | `DiagnosisEntryPanel`/`ConclusionPanel`(双 Gauge+根因卡)/`EvidenceTimeline`/`ServiceTopology`/`SuggestionChecklist` |
| reports | `ReportTimeline`/`ReportRiskPanel`(Gauge)/`ReportSections`/`RelationInsightCard`/`StageRing` |
| alerts | `AlertBoard`(三态 StatCard)/`AlertTable`/`AlertDetailDrawer` |
| trace | `TraceSearchBar`/`TraceWaterfall` |
| funnel | `FunnelMain`(FunnelChart)/`LossLocator` |

### 2. 占位规范（智能体耦合硬性规则）

- 所有智能体产出区块在 F1 用 `EmptyState` 占位，并预留版式化结构（结论卡/三段式/阶段环），**禁止对话框/聊天气泡形态**。
- 数值类（severity/confidence/risk_level）预留 `GaugeChart` 仪表位。
- `node_trace` 仅通过 `StageRing` 占位，不出现节点函数名/模型名。

### 3. 约束

- 不直接 `import echarts`；不直接 `axios`/`fetch`。
- 真实数据接入留待 F5（诊断/链路）、F6（报告/预警）、F7（关系洞察）。
- 简体中文文案。

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 5 页可达 | `/analysis/*` 5 个路由均渲染不报错 |
| AC-02 | 分区 | 各页按 §3.3~§3.7 编排占位 |
| AC-03 | 耦合规范 | 无对话框形态；数值预留仪表；node_trace 仅 StageRing |

## 完成定义（DoD）

- [ ] 仅修改 analysis 视图与 analysis-* 组件目录
- [ ] 不修改 DEV.md

## 下游消费说明（供其他 Agent 只读）

- F1-16 router 注册 5 个 `/analysis/*`
- F5/F6/F7 替换占位为真实可视化
