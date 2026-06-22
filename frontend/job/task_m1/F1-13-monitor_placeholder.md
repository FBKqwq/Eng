# F1-13：日志监控 7 子页占位 monitor_placeholder

## Agent 角色

监控页骨架专项 Agent — **仅实现监控三段式骨架 + 7 子页配置驱动占位**。

## 唯一负责文件/目录

```
src/components/monitor/LogMonitorShell.vue
src/components/monitor/DynamicFilterBar.vue
src/components/monitor/ChartBand.vue
src/views/monitor/application.vue
src/views/monitor/behavior.vue
src/views/monitor/web-server.vue
src/views/monitor/performance.vue
src/views/monitor/security.vue
src/views/monitor/infrastructure.vue
src/views/monitor/audit.vue
```

## 禁止修改

- `components/common/`、`utils/logTypeMeta.js`（只 import）、其他页面目录、`router/index.js`

## 前置依赖

- F1-04 `getLogTypeMeta`
- F1-05 charts、F1-06 common（`LogTable`/`EmptyState`）

## 开发要求

### 1. `LogMonitorShell.vue`（7 子页共用骨架）

三段式：筛选区（`DynamicFilterBar`）+ 图表带（`ChartBand`）+ 明细区（`LogTable`）。
props：`logType`、`chartTemplates`、`defaultColumns`。

### 2. 骨架内私有件（F1 占位）

| 组件 | 占位形式 |
| --- | --- |
| `DynamicFilterBar` | `EmptyState`，标注「待后端字段目录接口 `GET /logs/fields`」 |
| `ChartBand` | 无模板时 `EmptyState`，`pending-api="metrics 六类聚合接口"` |

### 3. 7 个子页 view

每个 view 仅：调用 `getLogTypeMeta(key)` 取配置 + 渲染 `LogMonitorShell`，**不复制页面代码**。
key 与文件：application / behavior / web-server / performance / security / infrastructure / audit。

### 4. 约束

- 差异走配置对象（来自 logTypeMeta），不复制组件。
- `LogTable` 真实查询留待 F2；F1 仅占位。
- 简体中文文案。

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 7 子页可达 | `/monitor/*` 7 个路由均渲染不报错 |
| AC-02 | 骨架复用 | 7 子页共用 `LogMonitorShell`，差异来自配置 |
| AC-03 | 占位标注 | 筛选/图表带用 `EmptyState` + pending 标注 |

## 完成定义（DoD）

- [ ] 仅修改 monitor 视图与组件
- [ ] 不修改 DEV.md

## 下游消费说明（供其他 Agent 只读）

- F1-16 router 注册 7 个 `/monitor/*`
- F2 接 `logs/search`/`logs/fields`，F4 接聚合图表带
