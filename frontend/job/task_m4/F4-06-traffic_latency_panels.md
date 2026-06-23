# F4-06：流量与耗时面板 traffic_latency_panels

## Agent 角色

驾驶舱图表 Agent — **流量+错误叠加与耗时多系列趋势**。

## 唯一负责文件

```
src/components/dashboard/TrafficErrorPanel.vue
src/components/dashboard/LatencyPanel.vue
```

## 禁止修改

- views、api、charts 底层封装

## 前置依赖

- F4-02 `useMetrics`
- F1-05 `TrendChart`、`BarChart`

## 开发要求

### 1. TrafficErrorPanel

- `queryTraffic` + `queryErrors`（application + web_server 口径按后端契约）
- 面积折线请求量 + 错误量柱状叠加
- 错误分布：Top N 服务/error_code 横条 + 环形图并排

### 2. LatencyPanel

- `queryLatency`：avg / p95 / p99 多系列折线

### 3. 共性

- inject 时间窗；loading/empty/error 统一
- mock 角标；图表过渡动画（F7-04 可审计）

### 4. 约束

- 两文件同属本任务，**禁止**其他 Agent 修改

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 流量 | 趋势+错误叠加可见 |
| AC-02 | 错误分布 | 横条+环形并排 |
| AC-03 | 耗时 | 三系列折线 |
| AC-04 | 联动 | 时间窗刷新 |

## 完成定义（DoD）

- [ ] 仅修改上述两个 vue 文件
- [ ] 更新 STATUS F4-06 行

## 下游消费说明

- F4-07 驾驶舱装配
