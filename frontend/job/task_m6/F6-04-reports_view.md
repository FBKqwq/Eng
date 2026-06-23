# F6-04：报告页装配 reports_view

## Agent 角色

页面装配 Agent — **左右栏报告浏览**。

## 唯一负责文件

```
src/views/analysis/reports.vue
```

## 禁止修改

- analysis-reports 子组件（只组合）

## 前置依赖

- F6-01、F6-03

## 开发要求

### 1. 布局

- 左：ReportTimeline
- 右：ReportRiskPanel + ReportSections
- 选中报告 → getReportDetail

### 2. 数据

- mount 拉 recent；默认选中最新
- loading/error；mock 角标读 api USE_MOCK

### 3. 约束

- RelationInsightCard 占位或 F7 再接

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 列表 | 时间轴有数据 |
| AC-02 | 详情 | 选中后右栏更新 |
| AC-03 | 空态 | 无报告 EmptyState |
| AC-04 | 构建 | 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `reports.vue`
- [ ] 更新 STATUS F6-04 行

## 下游消费说明

- 驾驶舱 LatestReportCard 跳转本页
