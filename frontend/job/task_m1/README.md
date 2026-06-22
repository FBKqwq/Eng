# F1 骨架重构 — 前端 Agent 任务编排说明

> 对应总体规划：`location/frontend/前端开发总体规划.md` §1、§4、§7（阶段 F1）
> 目标：树状目录 + 双栏布局 + 新路由树 + 时间窗 composable + ECharts 基础件 + 通用组件 + API wrapper 骨架 + 全部页面空页占位，构建通过、可导航。
> 原则：**一个 Agent 只负责一组互不重叠的文件**，避免多人同时改同一文件造成冲突。
> 边界：本里程碑只涉及 `location/frontend/`，不修改 backend、docker-compose、elasticsearch、logstash、kibana、setup。

---

## 1. 阶段定位

F1 是前端重构的地基阶段，只交付「骨架 + 占位」，不接真实业务数据：

- 树状侧边栏可导航全部 16 个页面，每个页面以空页/`EmptyState` 占位。
- `npm run build` 通过。
- 全局时间窗、预警角标、链路健康微状态等跨页机制就位。
- 图表层（ECharts 薄封装）与通用展示组件就位，但只渲染空态/占位。
- 7 个「待后端」接口先落 wrapper 函数签名 + `USE_MOCK` 空数据，页面走真实调用路径。

F1 **不做**：监控日志表真实查询（F2）、系统页能力迁移（F3）、聚合图表数据接入（F4）、诊断/链路可视化（F5）、报告/预警接入（F6）、关系洞察等增强（F7）。

---

## 2. 任务清单与文件归属

| 任务编号 | 文档 | 唯一负责文件/目录 | 禁止修改 |
| --- | --- | --- | --- |
| F1-01 | [F1-01-design_tokens.md](./F1-01-design_tokens.md) | `src/assets/styles/index.css` | 其他所有文件 |
| F1-02 | [F1-02-composables.md](./F1-02-composables.md) | `src/composables/useTimeRange.js`、`src/composables/usePolling.js` | 其他所有文件 |
| F1-03 | [F1-03-api_wrappers.md](./F1-03-api_wrappers.md) | `src/api/request.js`、`logs.js`、`metrics.js`、`diagnosis.js`、`reports.js`、`alerts.js`、`system.js` | 其他所有文件 |
| F1-04 | [F1-04-utils.md](./F1-04-utils.md) | `src/utils/format.js`、`src/utils/logTypeMeta.js` | 其他所有文件 |
| F1-05 | [F1-05-charts.md](./F1-05-charts.md) | `src/components/common/charts/*`（BaseChart/Gauge/Trend/Bar/Pie/Funnel） | 其他所有文件 |
| F1-06 | [F1-06-common_components.md](./F1-06-common_components.md) | `src/components/common/*`（EmptyState/StatCard/StatusCard/SeverityBadge/LogTable/TimeAxis/StageRing） | charts/ 子目录及其他文件 |
| F1-07 | [F1-07-menu.md](./F1-07-menu.md) | `src/layout/menu.js` | 其他所有文件 |
| F1-08 | [F1-08-sidebar_tree.md](./F1-08-sidebar_tree.md) | `src/layout/components/SidebarTree.vue`、`SidebarTreeNode.vue` | 其他所有文件 |
| F1-09 | [F1-09-topbar.md](./F1-09-topbar.md) | `src/layout/components/TopBar.vue` | 其他所有文件 |
| F1-10 | [F1-10-pipeline_health_dot.md](./F1-10-pipeline_health_dot.md) | `src/layout/components/PipelineHealthDot.vue` | 其他所有文件 |
| F1-11 | [F1-11-layout_shell.md](./F1-11-layout_shell.md) | `src/layout/index.vue` | 其他所有文件 |
| F1-12 | [F1-12-dashboard_placeholder.md](./F1-12-dashboard_placeholder.md) | `src/views/dashboard/`、`src/components/dashboard/` | 其他所有文件 |
| F1-13 | [F1-13-monitor_placeholder.md](./F1-13-monitor_placeholder.md) | `src/views/monitor/`（7 页）、`src/components/monitor/` | 其他所有文件 |
| F1-14 | [F1-14-analysis_placeholder.md](./F1-14-analysis_placeholder.md) | `src/views/analysis/`（5 页）、`src/components/analysis-*/` | 其他所有文件 |
| F1-15 | [F1-15-system_placeholder.md](./F1-15-system_placeholder.md) | `src/views/system/`（3 页）、`src/components/system/` | 其他所有文件 |
| F1-16 | [F1-16-router.md](./F1-16-router.md) | `src/router/index.js` | 其他所有文件 |
| F1-17 | [F1-17-dev_docs.md](./F1-17-dev_docs.md) | `frontend/DEV.md` | 业务代码文件 |

---

## 2.1 目录树与路由（落地基线）

```text
总览驾驶舱                 /dashboard
日志监控
├── 应用服务日志           /monitor/application
├── 用户行为日志           /monitor/behavior
├── Web服务器日志          /monitor/web-server
├── 性能指标日志           /monitor/performance
├── 安全日志               /monitor/security
├── 基础设施日志           /monitor/infrastructure
└── 审计日志               /monitor/audit
智能分析
├── 异常诊断中心           /analysis/diagnosis
├── 周期体检报告           /analysis/reports
├── 预警中心               /analysis/alerts
├── 调用链路追踪           /analysis/trace
└── 业务漏斗洞察           /analysis/funnel
系统运维
├── 链路健康与验证         /system/pipeline
├── 组件运行状态           /system/components
└── 配置快照               /system/config
```

旧路由重定向：`/` → `/dashboard`，`/monitor` → `/monitor/application`，`/diagnosis` → `/analysis/diagnosis`，`/results` → `/analysis/reports`，`/system` → `/system/components`；`/temp/developer` 复用 `/system/components` 视图。

---

## 3. 推荐执行顺序

```text
阶段 A（无依赖，可并行，最多 4 Agent）
  F1-01 design_tokens      ← 设计令牌/全局样式，越早越好
  F1-02 composables        ← useTimeRange / usePolling
  F1-03 api_wrappers       ← 7 个 wrapper + USE_MOCK
  F1-04 utils              ← format / logTypeMeta

阶段 B（依赖 A-01；图表依赖 echarts 依赖项）
  F1-05 charts             ← ECharts 薄封装（BaseChart + 5 图表）
  F1-06 common_components  ← EmptyState/StatCard/... 通用件

阶段 C（布局，依赖 A 与 B）
  F1-07 menu               ← 目录声明数据（无依赖，可提前）
  F1-08 sidebar_tree       ← 依赖 F1-07
  F1-09 topbar             ← 依赖 F1-02、F1-03
  F1-10 pipeline_health    ← 依赖 F1-03
  F1-11 layout_shell       ← 依赖 F1-08/09/10、F1-02

阶段 D（页面占位，依赖 B 通用件，可并行 4 Agent）
  F1-12 dashboard 占位
  F1-13 monitor 占位
  F1-14 analysis 占位
  F1-15 system 占位

阶段 E（路由汇总，依赖 D 全部页面存在）
  F1-16 router             ← 16 路由 + 旧路由重定向 + meta.title

阶段 F（全部完成后）
  F1-17 dev_docs           ← 收敛 frontend/DEV.md，避免多人同改
```

---

## 4. 跨任务约定（所有 Agent 必须遵守）

1. **只改自己负责的文件/目录**；需要别人提供的能力时按接口约定调用，不得越权修改。
2. **页面与组件不得直接 `axios`/`fetch`**，统一通过 `src/api/*.js`。
3. **前端不得直接访问 ES、Kafka、Docker、Kibana API**，所有数据走后端接口。
4. **图表只进不出**：ECharts 实例只允许存在于 `components/common/charts/`，页面组件传 data/option，不直接 `import echarts`。
5. **新增依赖仅 ECharts 一项**；不引入 Pinia、UI 组件库等大型依赖。
6. **占位即占位**：F1 阶段所有业务区块用 `EmptyState` 占位，标注待接入信息或 `pending-api`；mock 数据须可识别为「演示数据」，禁止冒充真实数据。
7. 全部中文使用**简体中文**；除非负责人明确要求，**不要 commit**。

---

## 5. F1 总体验收（全部任务完成后）

- [ ] `npm run build` 通过（无报错）。
- [ ] 侧边栏树状目录可导航全部 16 个页面，命中叶子高亮、父分组自动展开。
- [ ] 顶部条展示路由 `meta.title`、全局时间范围选择器、活跃预警角标（轮询）。
- [ ] aside 底部链路健康微状态点可渲染并跳转 `/system/pipeline`。
- [ ] 旧路由 `/`、`/monitor`、`/diagnosis`、`/results`、`/system` 正确重定向。
- [ ] 6 个图表薄封装可在无数据时显示空态，不报错。
- [ ] `metrics.js`/`alerts.js`/`reports.js` 的 `USE_MOCK=true` 返回契约化空数据，页面走真实调用路径。
- [ ] `frontend/DEV.md` 已更新为新路由/目录/约束基线。

---

## 6. 基础设施与依赖声明

- 后端聚合（metrics 六模板）、reports、alerts、logs/fields 接口未就绪不阻塞 F1；相关区块以 `EmptyState` 占位并标注 `pending-api`。
- `logs/search`、`system/status`、`system/pipeline/verify`、`health`、`diagnosis` 后端已有，F1 仅落 wrapper，不在 F1 接入页面真实渲染（留待 F2/F3/F5）。
- 旧页面 `views/home`、`views/monitor/index`、`views/diagnosis/index`、`views/results`、`views/system/index` 在 F1 不删除，仅不再被新路由引用；其能力迁移分别由 F3（系统）、F5（诊断）承接。
