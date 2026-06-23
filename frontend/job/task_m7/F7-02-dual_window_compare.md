# F7-02：双窗口对比 dual_window_compare

## Agent 角色

对比增强 Agent — **StatCard 环比 + 漏斗时段对比 tab**。

## 唯一负责文件

```
src/components/common/StatCard.vue
src/views/analysis/funnel.vue
```

## 禁止修改

- `FunnelMain.vue`、`LossLocator.vue`（在 funnel.vue 内加 tab 编排）
- api（可调 metrics 对比接口若已封装）

## 前置依赖

- F4-05 HealthOverview 使用 StatCard
- F4-08 funnel 页
- 后端 `es_compare_time_windows` 或 metrics 对比参数

## 开发要求

### 1. StatCard 扩展

- 新增 props：`delta`、`deltaDirection`（up/down/flat）
- 后端对比未就绪时 **不渲染** 箭头（默认 hidden）
- 数值格式化用 `format.js`

### 2. funnel.vue 时段对比 tab

- 启用第二个 tab「时段对比」（原 F4 隐藏）
- 双漏斗并排：当前窗 vs 对比窗
- 对比 API 未就绪：tab 整个 `v-if="false"` 或 disabled + tooltip

### 3. 数据

- inject `useTimeRange`；对比窗可由 TopBar 扩展或固定「上一等长窗口」
- 不自创聚合口径

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 环比 | API 就绪时箭头显示 |
| AC-02 | 未就绪 | 无箭头/tab 隐藏 |
| AC-03 | 双漏斗 | 对比 tab 数据正确 |
| AC-04 | 构建 | 通过 |

## 完成定义（DoD）

- [ ] 仅修改 StatCard + funnel.vue
- [ ] 更新 STATUS F7-02 行

## 下游消费说明

- HealthOverview 传入 delta；驾驶舱体验增强
