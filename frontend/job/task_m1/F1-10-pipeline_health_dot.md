# F1-10：链路健康微状态 pipeline_health_dot

## Agent 角色

链路健康微状态专项 Agent — **仅实现 aside 底部的链路健康状态点**。

## 唯一负责文件

```
src/layout/components/PipelineHealthDot.vue
```

## 禁止修改

- `system.js`（只 import）、`layout/index.vue`、`SidebarTree.vue`、`TopBar.vue`

## 前置依赖

- F1-03 `system.js` 的 `getSystemStatus`
- 可选 F1-02 `usePolling`
- 必读：`frontend/job/API_CONTRACT.md` §4.1；`F3-02` 的 `derivePipelineHealthTone(status)`（若已落地则 import utils，否则本组件内按契约内联）

## 开发要求

### 1. 状态点

- 轮询 `getSystemStatus()`（60s），解包后读 `res.data`（信封已由 `request.js` 处理）
- 按 **嵌套字段** 折算绿/黄/红/灰四态（**禁止**读不存在的 `overall` / `pipeline_healthy`）：
  - 绿：Kafka、ES 专项 `available===true` 且关键容器 `running`
  - 黄：部分可用或 ES `cluster_status` 为 yellow
  - 红：专项 `available===false` 且容器非 running
  - 灰：请求失败或无数据
- 颜色复用 F1-01 语义色令牌。
- 固定在 aside 底部（`margin-top:auto`），点击跳转 `/system/pipeline`。
- `title` 提示当前态文案。

### 2. 约束

- 不直接 `axios`/`fetch`；失败时降级为灰态，不报错。
- 简体中文文案。

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 轮询 | 调 `getSystemStatus`，60s 周期 |
| AC-02 | 四态 | 绿/黄/红/灰映射正确 |
| AC-03 | 跳转 | 点击跳 `/system/pipeline` |
| AC-04 | 容错 | 失败显示灰态，不报错 |

## 完成定义（DoD）

- [ ] 仅修改 `PipelineHealthDot.vue`
- [ ] 不修改 DEV.md

## 下游消费说明（供其他 Agent 只读）

- F1-11 layout 在 aside 底部挂载本组件
