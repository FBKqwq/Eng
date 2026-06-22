# F1-02：组合式函数 composables

## Agent 角色

跨页面逻辑复用专项 Agent — **仅实现全局时间窗与统一轮询两个组合式函数**。

## 唯一负责文件

```
src/composables/useTimeRange.js
src/composables/usePolling.js
```

## 禁止修改

- `layout/`、`components/`、`views/`、`api/` 等任何其他文件

## 前置依赖

- 无

## 开发要求

### 1. `useTimeRange.js`

提供全局时间窗口，供顶部条选择、各页面图表/列表共用同一窗口。

- 预设项：近 15 分钟 / 1 小时 / 6 小时 / 24 小时 / 自定义。
- 采用 `provide`/`inject` 模式：
  - `provideTimeRange()`：在 `layout/index.vue` 顶层调用，注入响应式状态。
  - `useTimeRange()`：页面/组件消费，返回 `{ presets, preset, setPreset, range }`。
- `range` 暴露可用于查询的 `{ start, end }`（计算属性，随 preset 变化）。

### 2. `usePolling.js`

统一轮询封装，供预警角标、链路健康点等使用。

- 签名：`usePolling(fn, intervalMs)`，返回 `{ start, stop }` 或在 `onMounted` 自动启动、`onUnmounted` 自动清理。
- 必须在组件卸载时清除定时器，避免内存泄漏。

### 3. 约束

- 纯组合式函数，不依赖任何业务组件。
- 简体中文注释。

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | provide/inject | `provideTimeRange()` + `useTimeRange()` 配套可用 |
| AC-02 | 预设 | `presets` 含 5 个预设项 |
| AC-03 | range | 切换 preset 后 `range` 计算值随之变化 |
| AC-04 | 轮询清理 | `usePolling` 在卸载时清除定时器 |

## 完成定义（DoD）

- [ ] 仅修改两个 composable 文件
- [ ] 不修改 DEV.md

## 下游消费说明（供其他 Agent 只读）

- F1-09 TopBar 调用 `useTimeRange().setPreset` 与 `presets`
- F1-11 layout 调用 `provideTimeRange()`
- F1-09/F1-10 可用 `usePolling` 实现 30s/60s 轮询
