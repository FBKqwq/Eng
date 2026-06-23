# F4-08：漏斗页 funnel_page

## Agent 角色

分析可视化 Agent — **五步漏斗 + 流失定位 + 页面装配**。

## 唯一负责文件

```
src/components/analysis-funnel/FunnelMain.vue
src/components/analysis-funnel/LossLocator.vue
src/views/analysis/funnel.vue
```

## 禁止修改

- api、charts 底层、其他 analysis 页

## 前置依赖

- F4-02 `useMetrics`（behavior_funnel）
- F1-05 `FunnelChart`、`BarChart`
- F2 监控跳转（预置筛选 query 约定）

## 开发要求

### 1. FunnelMain

- 五步：page_view → product_click → add_to_cart → checkout_click → pay_button_click
- 转化率标注；流失超阈值步骤橙/红
- `queryBehaviorFunnel` 驱动

### 2. LossLocator

- 选中异常步骤后展示 Top 错误码横条
- 「查看应用日志」→ `/monitor/application` 带预置 filters query

### 3. funnel.vue

- 组合 FunnelMain + LossLocator
- 时段对比 tab **默认隐藏**（F7-02 启用）
- inject 时间窗

### 4. 约束

- 符合 §3.7；禁止对话框式输出

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 漏斗 | 五步与转化率可见 |
| AC-02 | 流失 | 选步后 LossLocator 有数据 |
| AC-03 | 跳转 | 可带筛选跳监控页 |
| AC-04 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改上述三个文件
- [ ] 更新 STATUS F4-08 行

## 下游消费说明

- F7-02 双漏斗时段对比
