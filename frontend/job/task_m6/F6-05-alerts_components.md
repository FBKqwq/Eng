# F6-05：预警组件 alerts_components

## Agent 角色

预警交互 Agent — **看板 + 表格 + 详情抽屉**。

## 唯一负责文件

```
src/components/analysis-alerts/AlertBoard.vue
src/components/analysis-alerts/AlertTable.vue
src/components/analysis-alerts/AlertDetailDrawer.vue
```

## 禁止修改

- api、views、TopBar

## 前置依赖

- F6-02 schema
- F1-06 SeverityBadge

## 开发要求

### 1. AlertBoard

- active / acknowledged / resolved 三态计数卡
- 24h 预警数量趋势迷你图（可用 mock 序列）

### 2. AlertTable

- 列：类型、severity、服务、首次/最近时间、evidence_count
- active 行「确认」按钮 → emit ack
- severity 色块

### 3. AlertDetailDrawer

- 右侧抽屉：解释文案三段（现象/影响/建议）
- 关联证据列表、报告链接
- 「发起深度诊断」→ emit 跳转 diagnosis

### 4. 约束

- 版式化文案，非对话

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 看板 | 三态计数 |
| AC-02 | 表格 | 列表+确认按钮 |
| AC-03 | 抽屉 | 三段解释+诊断按钮 |
| AC-04 | 构建 | 通过 |

## 完成定义（DoD）

- [ ] 仅修改上述三个 vue 文件
- [ ] 更新 STATUS F6-05 行

## 下游消费说明

- F6-06 alerts.vue
