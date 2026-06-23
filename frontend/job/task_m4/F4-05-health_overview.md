# F4-05：健康总览 HealthOverview

## Agent 角色

驾驶舱组件 Agent — **健康仪表 + 核心指标数字带**。

## 唯一负责文件

```
src/components/dashboard/HealthOverview.vue
```

## 禁止修改

- 其他 dashboard 组件、views

## 前置依赖

- F4-02 `useMetrics`（traffic/errors/latency 组合折算健康分）
- F1-05 `GaugeChart`、F1-06 `StatCard`

## 开发要求

### 1. 健康分

- 前端按权重折算：错误率、链路状态（可读 system 或占位）、活跃预警数（F4 可 mock 0）
- 大号 `GaugeChart` 绿/黄/红三段

### 2. 指标带

- 5 个 `StatCard`：日志总量、错误率、平均响应、P95、活跃预警数
- 环比箭头：后端双窗口未就绪时**隐藏**箭头（F7-02 再接）

### 3. 数据

- 多模板 `useMetrics` 并行；loading 统一
- mock 角标

### 4. 约束

- 符合总体规划 §3.1；数值先于文字

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 仪表 | Gauge 随数据更新 |
| AC-02 | 五卡 | 五指标有值或占位 |
| AC-03 | 时间窗 | range 变更刷新 |
| AC-04 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `HealthOverview.vue`
- [ ] 更新 STATUS F4-05 行

## 下游消费说明

- F4-07 `dashboard/index.vue` 组合
