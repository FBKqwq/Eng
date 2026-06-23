# F4-03：图表带 ChartBand

## Agent 角色

监控可视化 Agent — **配置驱动 2~3 个聚合图表真实渲染**。

## 唯一负责文件

```
src/components/monitor/ChartBand.vue
```

## 禁止修改

- `LogMonitorShell.vue`、views、logTypeMeta（只读 chartTemplates）

## 前置依赖

- F4-02 `useMetrics`
- F4-04 `chartTemplates` 配置
- F1-05 charts 组件

## 开发要求

### 1. Props

- `logType` — 查 meta 得 `chartTemplates`
- 每项 template：`{ template, title, chartType, seriesMapping }`

### 2. 行为

- 每个模板独立 `useMetrics` 实例（或等价并行 fetch）
- loading：骨架；error：EmptyState + 重试
- mock：`isMock` 时角标「演示数据」

### 3. 图表映射

- 使用 `TrendChart` / `BarChart` / `PieChart` 等 common/charts
- **禁止** import echarts

### 4. 替换 F1/F2 占位

- 移除「pending-api metrics」纯占位，改为真实数据路径（接口离线仍 EmptyState）

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 配置驱动 | chartTemplates 决定图表数量 |
| AC-02 | 聚合 | 数据来自 useMetrics |
| AC-03 | 时间窗 | 随全局 range 刷新 |
| AC-04 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `ChartBand.vue`
- [ ] 更新 STATUS F4-03 行

## 下游消费说明

- F2-06 Shell 无需改动即可展示真实图表带
