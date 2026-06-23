# F2-07：监控七子页视图 monitor_views

## Agent 角色

页面装配 Agent — **确保 7 个子页正确传入 logType 配置**。

## 唯一负责文件

```
src/views/monitor/application.vue
src/views/monitor/behavior.vue
src/views/monitor/web-server.vue
src/views/monitor/performance.vue
src/views/monitor/security.vue
src/views/monitor/infrastructure.vue
src/views/monitor/audit.vue
```

## 禁止修改

- `components/`、`router/`、`api/`、`utils/logTypeMeta.js`（只 import）

## 前置依赖

- F2-05 meta 键名稳定
- F2-06 Shell 可用

## 开发要求

### 1. 每个 view 结构

```vue
<LogMonitorShell :log-type="meta.logType" />
```

- 通过 `getLogTypeMeta('<key>')` 取 meta（若 Shell 内部自取则可仅传 key）
- **禁止复制页面逻辑**；差异仅在 key 字符串

### 2. 约束

- 不新增业务组件；不直接 axios
- 保持与 F1-16 路由 path 一致

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 七路由 | 7 页均可打开且渲染 Shell |
| AC-02 | 配置驱动 | 无重复大段模板代码 |
| AC-03 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改上述 7 个 view
- [ ] 更新 STATUS F2-07 行
