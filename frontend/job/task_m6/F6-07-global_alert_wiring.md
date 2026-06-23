# F6-07：全局预警与摘要接线 global_alert_wiring

## Agent 角色

全局集成 Agent — **TopBar 角标 + 驾驶舱摘要卡真实数据**。

## 唯一负责文件

```
src/layout/components/TopBar.vue
src/components/dashboard/AlertDigest.vue
src/components/dashboard/LatestReportCard.vue
```

## 禁止修改

- api 文件（只调用）
- 其他 layout 组件

## 前置依赖

- F6-01、F6-02（USE_MOCK=false 切换）
- F4-07 已有摘要 UI
- F1-02 `usePolling` 30s

## 开发要求

### 1. TopBar

- 轮询 `getActiveAlerts` 30s（`usePolling`）
- 解包后：`alertCount = res.data?.total ?? res.data?.items?.length ?? 0`（见 `API_CONTRACT.md` §4.4）
- 数字 > 0 红点；点击跳转 `/analysis/alerts`
- `catch` 失败角标为 0；可读 `e.error?.code` 打日志

### 2. AlertDigest

- 取 `getActiveAlerts` 的 `data.items` 前 5 条
- `USE_MOCK=false` 时移除「演示数据」角标

### 3. LatestReportCard

- `getRecentReports` → `data.items[0]`（`risk_level` + `summary`）
- 无报告：`items` 空数组时空态

### 4. 协调

- ack 后角标应下次轮询更新（或事件总线轻量 refresh，优先 polling）

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 角标 | TopBar 真实 active 数 |
| AC-02 | 摘要 | 驾驶舱两卡真实数据 |
| AC-03 | 跳转 | 角标/摘要跳转正确 |
| AC-04 | mock关 | USE_MOCK=false 无演示角标 |

## 完成定义（DoD）

- [ ] 仅修改上述三个文件
- [ ] 更新 STATUS F6-07 行

## 下游消费说明

- 全局用户体验闭环
