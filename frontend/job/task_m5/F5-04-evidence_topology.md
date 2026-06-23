# F5-04：证据链与拓扑 evidence_topology

## Agent 角色

诊断可视化 Agent — **证据时间轴 + 服务关系图 + 同类错误迷你图**。

## 唯一负责文件

```
src/components/analysis-diagnosis/EvidenceTimeline.vue
src/components/analysis-diagnosis/ServiceTopology.vue
```

## 禁止修改

- `TimeAxis.vue`（组合使用，不修改除非 bug）
- api、views

## 前置依赖

- F1-06 `TimeAxis`
- F1-05 `BarChart`（sparkline 迷你柱）
- F5-01 结果字段 evidence_logs、affected_services、similar_errors

## 开发要求

### 1. EvidenceTimeline

- 垂直时间轴：时间、服务、关键字段
- ERROR 节点红色高亮
- 基于 `TimeAxis` 或等价结构

### 2. ServiceTopology

- 简化拓扑：服务节点 + 连线
- 异常服务红色脉冲动画（克制，符合 reduced-motion）

### 3. ServiceTopology 内或 Timeline 旁

- 同类错误频次迷你柱状图（similar_errors）
- 展示是否集中爆发

### 4. 约束

- 纯 props 驱动；不调 API

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 时间轴 | 证据节点可读 |
| AC-02 | 拓扑 | 异常服务可辨识 |
| AC-03 | 迷你图 | similar_errors 可视化 |
| AC-04 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改上述两个 vue 文件
- [ ] 更新 STATUS F5-04 行

## 下游消费说明

- F5-06 中部下方证据区
