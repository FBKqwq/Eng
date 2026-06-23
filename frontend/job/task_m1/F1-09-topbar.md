# F1-09：顶部条 topbar

## Agent 角色

顶部条专项 Agent — **仅实现页面标题 + 全局时间范围选择器 + 活跃预警角标**。

## 唯一负责文件

```
src/layout/components/TopBar.vue
```

## 禁止修改

- `useTimeRange.js`/`usePolling.js`（只 import）、`alerts.js`（只 import）、`layout/index.vue`、`SidebarTree.vue`

## 前置依赖

- F1-02 `useTimeRange`（及可选 `usePolling`）
- F1-03 `alerts.js` 的 `getActiveAlerts`

## 开发要求

### 1. 标题

- 取当前路由 `meta.title`，无则回退「页面」。

### 2. 全局时间范围选择器

- 渲染 `useTimeRange().presets`，`change` 时调用 `setPreset`。
- 所有页面共用同一时间窗（由 composable 保证）。

### 3. 活跃预警角标

- 轮询 `getActiveAlerts()`（30s，建议用 `usePolling`）。
- 解包后计数：`const d = res.data; alertCount = d?.total ?? d?.items?.length ?? 0`（**禁止**假设 `data` 为顶层数组）。
- 数量 > 0 时红点；点击跳转 `/analysis/alerts`。
- 请求失败（含 `e.error?.code`）时角标归 0，不抛错。

### 4. 约束

- 不直接 `axios`/`fetch`。
- 简体中文文案。

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 标题 | 随路由 `meta.title` 变化 |
| AC-02 | 时间窗 | 选择器联动 `useTimeRange` |
| AC-03 | 角标 | 轮询 `getActiveAlerts`，>0 显示红点，可跳转 |
| AC-04 | 容错 | 请求失败角标为 0，不报错 |

## 完成定义（DoD）

- [ ] 仅修改 `TopBar.vue`
- [ ] 不修改 DEV.md

## 下游消费说明（供其他 Agent 只读）

- F1-11 layout 在 main 顶部挂载 `TopBar`
