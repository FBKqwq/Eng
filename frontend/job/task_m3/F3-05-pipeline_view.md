# F3-05：链路页编排 pipeline_view

## Agent 角色

页面装配 Agent — **链路健康与验证页数据拉取与组件组合**。

## 唯一负责文件

```
src/views/system/pipeline.vue
```

## 禁止修改

- `PipelineGraph.vue`、`VerifyOutputPanel.vue`（只组合）
- 其他 views、layout

## 前置依赖

- F3-01 `getSystemStatus`、`verifyPipeline`
- F3-02 `getPipelineNodes`
- F3-03、F3-04 组件就绪
- F1-02 `usePolling` 可选用于 status 轮询

## 开发要求

### 1. 数据流

- mount 时 `getSystemStatus` → 归一化 → 传给 `PipelineGraph`
- 用户触发验证 → `verifyPipeline({ workers })` → 结果传给 `VerifyOutputPanel`
- 验证完成后可选刷新 status

### 2. 布局

```text
[PipelineGraph]
[VerifyOutputPanel]
```

### 3. 错误态

- status 失败：图谱区 EmptyState + 重试
- verify 失败：面板展示错误，保留上次成功输出可选

### 4. 约束

- 不修改子组件源码
- aside `PipelineHealthDot` 行为不回归（F1 已有）

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 状态图 | 四节点随 status 着色 |
| AC-02 | 验证 | 一键验证有终端输出 |
| AC-03 | 错误 | 离线有结构化错误态 |
| AC-04 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `pipeline.vue`
- [ ] 更新 STATUS F3-05 行

## 下游消费说明

- 路由 `/system/pipeline`；F3-10 DEV 文档记录
