# F6-03：报告组件 reports_components

## Agent 角色

报告可视化 Agent — **时间轴 + 风险仪表 + 结构化拆解**。

## 唯一负责文件

```
src/components/analysis-reports/ReportTimeline.vue
src/components/analysis-reports/ReportRiskPanel.vue
src/components/analysis-reports/ReportSections.vue
```

## 禁止修改

- `RelationInsightCard.vue`（F7-01）
- api、views

## 前置依赖

- F6-01 schema
- F1-05 GaugeChart、F1-06 TimeAxis、StageRing（页脚由 ReportSections 或 view 组合）

## 开发要求

### 1. ReportTimeline

- 左栏倒序列表：时间、risk_level 色点、报告类型
- `@select` 选中报告 id

### 2. ReportRiskPanel

- 三色风险仪表 + 定级理由摘要
- 窗口指标回放：三个迷你趋势（报告内 metrics_snapshot）

### 3. ReportSections

- 分节卡片：总体结论 / 异常发现 / 业务洞察
- 标题 + 要点列表版式
- 页脚 node_trace 阶段点（可用 StageRing 迷你模式或一行阶段点）
- 降级报告「统计模式」灰色角标

### 4. 约束

- 禁止聊天气泡；§5 合规

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 时间轴 | 可选中报告 |
| AC-02 | 风险 | 仪表+理由 |
| AC-03 | 拆解 | 三节要点列表 |
| AC-04 | 阶段 | node_trace 可见 |

## 完成定义（DoD）

- [ ] 仅修改上述三个 vue 文件
- [ ] 更新 STATUS F6-03 行

## 下游消费说明

- F6-04 reports.vue
