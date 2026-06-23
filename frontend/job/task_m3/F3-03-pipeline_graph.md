# F3-03：链路图 PipelineGraph

## Agent 角色

系统可视化 Agent — **四节点横向链路图与状态着色**。

## 唯一负责文件

```
src/components/system/PipelineGraph.vue
```

## 禁止修改

- views、api、其他 system 组件

## 前置依赖

- F3-02 `systemStatus.js`（`getPipelineNodes`）
- F1-06 设计令牌可用

## 开发要求

### 1. Props

- `nodes` — 来自 `getPipelineNodes` 的数组（label、status、detail?）
- `loading` — 可选骨架态

### 2. 视觉

- 横向：日志生产 → Kafka → Logstash → ES
- 节点圆角卡 + 流向箭头；状态映射语义色（绿/黄/红/灰）
- 节点可展示简短 detail tooltip

### 3. 交互

- 纯展示组件；验证按钮不在本组件（由 view 编排）
- 响应式：窄屏可纵向堆叠

### 4. 约束

- 不调 API；不引用 echarts
- 简体中文文案

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 四节点 | 四节点顺序与总体规划 §3.8 一致 |
| AC-02 | 着色 | healthy/degraded/down/unknown 有区分 |
| AC-03 | 数据驱动 | 仅 props 驱动，无内联 fetch |
| AC-04 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `PipelineGraph.vue`
- [ ] 更新 STATUS F3-03 行

## 下游消费说明

- F3-05 `pipeline.vue` 组合本组件与验证面板
