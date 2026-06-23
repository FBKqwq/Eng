# F4-07：驾驶舱装配 dashboard_assembly

## Agent 角色

页面装配 Agent — **驾驶舱布局编排；预警/报告卡 mock 与真实分界**。

## 唯一负责文件

```
src/views/dashboard/index.vue
src/components/dashboard/AlertDigest.vue
src/components/dashboard/LatestReportCard.vue
```

## 禁止修改

- `HealthOverview`、`TrafficErrorPanel`、`LatencyPanel`（只组合）
- api 文件（组件内可调 alerts/reports api，但**本任务负责人**可改 AlertDigest/LatestReportCard）

## 前置依赖

- F4-05、F4-06 已完成
- F1-03 `alerts.js` / `reports.js`（USE_MOCK 可能仍为 true）

## 开发要求

### 1. dashboard/index.vue

- 编排：HealthOverview → TrafficErrorPanel → LatencyPanel → AlertDigest → LatestReportCard
- 响应式栅格；区块间距符合设计令牌

### 2. AlertDigest

- 展示最近 5 条 active 预警（类型、服务、时间）
- 数据：`alerts.js` `getActiveAlerts`；`USE_MOCK` 时角标「演示数据」
- 点击行跳转 `/analysis/alerts`
- **真实数据切换留 F6-07**，本任务实现完整 UI 路径

### 3. LatestReportCard

- 最近周期报告 risk_level + 一句话摘要
- `reports.js` `getRecentReports`；mock 角标
- 点击跳转 `/analysis/reports`
- F6 再接真实列表

### 4. mock/real 分界

- 在组件内读取 api 层 `USE_MOCK` 或响应头，统一展示演示角标
- 禁止 mock 数据无标注

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 布局 | 五区块完整编排 |
| AC-02 | 图表区 | F4-05/06 正常嵌入 |
| AC-03 | 摘要区 | 预警/报告卡可点击跳转 |
| AC-04 | mock | 演示数据有角标 |

## 完成定义（DoD）

- [ ] 仅修改上述三个文件
- [ ] 更新 STATUS F4-07 行

## 下游消费说明

- F6-07 将 AlertDigest/LatestReportCard/TopBar 切真实数据
