# F3-06：通用状态卡 StatusCard

## Agent 角色

通用组件 Agent — **由 ServiceStatusCard 通用化为 StatusCard**。

## 唯一负责文件

```
src/components/common/StatusCard.vue
```

## 禁止修改

- views、旧 `ServiceStatusCard.vue`（本阶段不删除，可只读参考）
- api

## 前置依赖

- F1-06 占位 `StatusCard` 若存在则扩展
- F3-02 归一化数据结构约定

## 开发要求

### 1. Props

- `title`、`status`（healthy/degraded/down/unknown/offline）
- `detail` — 副文案或健康详情
- `port`、`container` — 可选元信息
- `loading` — 骨架

### 2. 视觉

- 状态色条/角标 + 标题 + detail
- 与 `SeverityBadge` 语义色令牌一致
- 卡片 hover 轻微阴影（F7-04 可再抛光）

### 3. 迁移对齐

- 能力覆盖旧 `ServiceStatusCard`：容器名、端口、健康文本
- 供 ≥2 处使用（components 页 + 未来扩展）

### 4. 约束

- 不调 API；纯展示

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 状态 | 五态视觉可区分 |
| AC-02 | 信息 | port/container/detail 可展示 |
| AC-03 | 通用 | 无页面硬编码业务名 |
| AC-04 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `StatusCard.vue`
- [ ] 更新 STATUS F3-06 行

## 下游消费说明

- F3-07 `components.vue` 状态卡矩阵
