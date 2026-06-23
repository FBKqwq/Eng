# F7-01：关系洞察卡 relation_insight

## Agent 角色

报告增强 Agent — **relation_chain 箭头卡 + 双指标对照迷你图**。

## 唯一负责文件

```
src/components/analysis-reports/RelationInsightCard.vue
```

## 禁止修改

- reports 其他组件、views（由 reports.vue 传入 props）

## 前置依赖

- F6-04 报告详情含 relation_chain 字段
- F1-05 TrendChart 迷你折线
- 后端 M7 relation 数据

## 开发要求

### 1. Props

- `relations` — relation_chain 数组（左指标、右指标、描述、series 数据）
- `visible` — 无数据时父级隐藏整块

### 2. 视觉

- 左指标 → 右指标箭头卡片
- 两侧各一条对照迷你折线图佐证
- 版式化要点，非对话

### 3. 降级

- 无 relation 数据：组件不渲染（v-if）
- mock 数据须角标（若仍 USE_MOCK）

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 箭头卡 | 关系描述可读 |
| AC-02 | 迷你图 | 双指标折线佐证 |
| AC-03 | 空数据 | 无数据不占位 |
| AC-04 | 构建 | 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `RelationInsightCard.vue`
- [ ] 更新 STATUS F7-01 行

## 下游消费说明

- `reports.vue` 右栏插入本卡（由 F6-04 或本任务后小改 reports.vue——**禁止** F7-01 改 reports.vue；若需插入点由负责人协调 F6-04 预留 slot，文档注明 reports 需含 `<RelationInsightCard>`）
