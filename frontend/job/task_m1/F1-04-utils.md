# F1-04：工具函数 utils

## Agent 角色

工具函数专项 Agent — **仅实现格式化工具与 7 类日志展示元数据**。

## 唯一负责文件

```
src/utils/format.js
src/utils/logTypeMeta.js
```

## 禁止修改

- `utils/systemStatus.js`（保留现状，归 F3/系统页相关任务）
- 其他任何文件

## 前置依赖

- 无（须对齐总体规划 §3.2 监控子页表）

## 开发要求

### 1. `format.js`

实现常用格式化：

- `formatTime(ts)`：时间戳/ISO → 本地可读时间。
- `formatBytes(n)`：字节 → KB/MB/GB。
- `formatPercent(n)`：小数 → 百分比文本。
- `formatDuration(ms)`：耗时 → 可读时长。

### 2. `logTypeMeta.js`

为 7 类日志维护展示元数据（名称、路由键、默认列、图表模板键、级别配色键）：

`application` / `behavior` / `web_server` / `performance` / `security` / `infrastructure` / `audit`

每类至少含：`logType`、`title`、`route`、`defaultColumns`、`chartTemplates`。
默认列与图表模板对齐总体规划 §3.2 表格。

导出 `getLogTypeMeta(key)` 供监控子页配置驱动使用。

### 3. 约束

- 纯函数/纯数据，不发请求、不依赖组件。
- 简体中文注释。

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 格式化 | 4 个 format 函数可用且边界安全（空值不报错） |
| AC-02 | 元数据 7 类 | `logTypeMeta` 覆盖 7 个 log_type |
| AC-03 | getLogTypeMeta | `getLogTypeMeta('application')` 返回含 defaultColumns/chartTemplates |
| AC-04 | 对齐规划 | 默认列与 §3.2 表一致 |

## 完成定义（DoD）

- [ ] 仅修改 `format.js`、`logTypeMeta.js`
- [ ] 不修改 DEV.md

## 下游消费说明（供其他 Agent 只读）

- F1-13 monitor 7 子页通过 `getLogTypeMeta(key)` 配置驱动差异
- F1-06 LogTable、各图表组件可用 format 工具
