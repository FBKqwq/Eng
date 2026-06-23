# F5-03：结论区 ConclusionPanel

## Agent 角色

诊断可视化 Agent — **严重度/置信度仪表 + 根因卡**。

## 唯一负责文件

```
src/components/analysis-diagnosis/ConclusionPanel.vue
```

## 禁止修改

- api、StageRing、其他面板

## 前置依赖

- F1-05 `GaugeChart`、F1-06 `SeverityBadge`
- 总体规划 §3.3、§5

## 开发要求

### 1. Props

- `result` — 诊断结果（可为 null 空态）
- `degraded` — 规则降级标记

### 2. 视觉

- 严重度四段半环仪表 + 置信度环形进度（中心百分数）
- `anomaly_type` 大号徽章 + `affected_services` 标签组
- 根因卡：「结论一句话（加粗）+ 推理依据要点列表」
- **禁止**聊天气泡

### 3. 降级

- `degraded` 时显示「基于规则判定」灰色角标
- 置信度可展示规则区间文案

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 仪表 | 严重度/置信度先于文字 |
| AC-02 | 根因卡 | 版式化非对话 |
| AC-03 | 降级 | 规则角标可见 |
| AC-04 | 空态 | 无结果时 EmptyState |

## 完成定义（DoD）

- [ ] 仅修改 `ConclusionPanel.vue`
- [ ] 更新 STATUS F5-03 行

## 下游消费说明

- F5-06 中部上方区块
