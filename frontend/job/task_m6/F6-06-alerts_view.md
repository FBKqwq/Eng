# F6-06：预警页装配 alerts_view

## Agent 角色

页面装配 Agent — **预警中心全流程**。

## 唯一负责文件

```
src/views/analysis/alerts.vue
```

## 禁止修改

- analysis-alerts 子组件（只组合）

## 前置依赖

- F6-02、F6-05

## 开发要求

### 1. 数据流

- getActiveAlerts 驱动看板+表
- ack → acknowledgeAlert → 刷新
- 抽屉选中行展示详情

### 2. 跳转

- 深度诊断 `router.push({ path: '/analysis/diagnosis', query: { alert_id } })`

### 3. 轮询

- 可选 30s 刷新（与 TopBar 协调，避免重复可 emit 事件——本页自刷新即可）

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 列表 | 预警可见 |
| AC-02 | ack | 确认后状态更新 |
| AC-03 | 抽屉 | 详情完整 |
| AC-04 | 诊断跳转 | query 正确 |

## 完成定义（DoD）

- [ ] 仅修改 `alerts.vue`
- [ ] 更新 STATUS F6-06 行

## 下游消费说明

- TopBar 角标跳转本页
