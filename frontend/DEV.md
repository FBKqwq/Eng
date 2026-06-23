# Frontend DEV 文档

## 1. 文档用途

本文档是 `location/frontend/` 目录级维护基线，用于说明 Vue 前端当前真实状态、路由约定、API 契约、系统状态页展示规则和本地开发验证方式。后续修改前端代码时，应同步更新本文档。

## 2. 前端定位

前端是 ELK + Kafka + LangGraph 电商日志分析项目的展示层，职责包括：

- 展示总览驾驶舱、日志监控（7 类）、智能分析（5 类）、系统运维（3 类）共 16 个业务页面。
- 通过后端 API 获取日志、诊断结果、系统状态与聚合指标。
- 不直接访问 Elasticsearch、Kafka、Docker 或 Kibana API。
- 为开发/排查提供 `/temp/developer` 手动入口，当前复用「组件运行状态」占位页。

## 3. 技术栈

| 类别 | 当前选型 |
| --- | --- |
| 框架 | Vue 3 |
| 构建工具 | Vite |
| 路由 | vue-router |
| HTTP | axios |
| 图表 | ECharts 5（仅 `components/common/charts/` 内引用） |
| 默认端口 | 5173 |

## 4. 目录职责

| 路径 | 职责 |
| --- | --- |
| `src/api/` | API wrapper（7 个模块 + `request.js`），页面不得直接 `axios`/`fetch` |
| `src/composables/` | 跨页组合式逻辑：`useTimeRange`（全局时间窗）、`usePolling`（轮询） |
| `src/views/dashboard/` | 总览驾驶舱页面 |
| `src/views/monitor/` | 日志监控 7 个子页（application、behavior、web-server 等） |
| `src/views/analysis/` | 智能分析 5 个子页（diagnosis、reports、alerts、trace、funnel） |
| `src/views/system/` | 系统运维 3 个子页（pipeline、components、config）；旧 `index.vue` 保留待 F3 迁移 |
| `src/components/common/` | 通用展示件：EmptyState、StatCard、StatusCard、SeverityBadge、LogTable、TimeAxis、StageRing |
| `src/components/common/charts/` | ECharts 薄封装：BaseChart、TrendChart、BarChart、PieChart、GaugeChart、FunnelChart |
| `src/components/dashboard/` | 驾驶舱区块组件 |
| `src/components/monitor/` | 监控页壳层与筛选/图表带（LogMonitorShell、DynamicFilterBar、ChartBand） |
| `src/components/analysis-*/` | 各分析子页专属组件（diagnosis、reports、alerts、trace、funnel） |
| `src/components/system/` | 系统运维区块（PipelineGraph、VerifyOutputPanel、ConfigSnapshotCard 等） |
| `src/layout/` | 双栏布局壳：`index.vue` |
| `src/layout/menu.js` | 侧边栏树状目录唯一配置源（新增页面须同步改此文件与路由） |
| `src/layout/components/` | SidebarTree、SidebarTreeNode、TopBar、PipelineHealthDot |
| `src/router/` | 路由定义（16 子路由 + 旧路由重定向 + `/temp/developer`） |
| `src/utils/` | `format.js`（格式化）、`logTypeMeta.js`（监控页配置驱动）、`systemStatus.js`（旧系统页兜底） |
| `src/assets/styles/` | 设计令牌与全局样式（`index.css`） |

## 5. 当前路由

F1 落地后的路由树（与 `src/layout/menu.js`、`src/router/index.js` 一致）：

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

| 路径 | 视图组件 | `meta.title` | 入口 |
| --- | --- | --- | --- |
| `/dashboard` | `views/dashboard/index.vue` | 总览驾驶舱 | 侧边栏 |
| `/monitor/application` | `views/monitor/application.vue` | 应用服务日志 | 侧边栏 |
| `/monitor/behavior` | `views/monitor/behavior.vue` | 用户行为日志 | 侧边栏 |
| `/monitor/web-server` | `views/monitor/web-server.vue` | Web服务器日志 | 侧边栏 |
| `/monitor/performance` | `views/monitor/performance.vue` | 性能指标日志 | 侧边栏 |
| `/monitor/security` | `views/monitor/security.vue` | 安全日志 | 侧边栏 |
| `/monitor/infrastructure` | `views/monitor/infrastructure.vue` | 基础设施日志 | 侧边栏 |
| `/monitor/audit` | `views/monitor/audit.vue` | 审计日志 | 侧边栏 |
| `/analysis/diagnosis` | `views/analysis/diagnosis.vue` | 异常诊断中心 | 侧边栏 |
| `/analysis/reports` | `views/analysis/reports.vue` | 周期体检报告 | 侧边栏 |
| `/analysis/alerts` | `views/analysis/alerts.vue` | 预警中心 | 侧边栏 |
| `/analysis/trace` | `views/analysis/trace.vue` | 调用链路追踪 | 侧边栏 |
| `/analysis/funnel` | `views/analysis/funnel.vue` | 业务漏斗洞察 | 侧边栏 |
| `/system/pipeline` | `views/system/pipeline.vue` | 链路健康与验证 | 侧边栏 |
| `/system/components` | `views/system/components.vue` | 组件运行状态 | 侧边栏 |
| `/system/config` | `views/system/config.vue` | 配置快照 | 侧边栏 |
| `/temp/developer` | `views/system/components.vue`（复用） | — | 手动访问，开发排查 |

**旧路由重定向**（`src/router/index.js` 内声明，勿删除）：

| 旧路径 | 重定向目标 |
| --- | --- |
| `/` | `/dashboard` |
| `/monitor` | `/monitor/application` |
| `/diagnosis` | `/analysis/diagnosis` |
| `/results` | `/analysis/reports` |
| `/system` | `/system/components` |

注意：历史文档中出现过 `/state/*` 路由约定，当前源码已不使用。旧单页 `views/home`、`views/monitor/index`、`views/diagnosis/index`、`views/results/index` 在 F1 不再被新路由引用，能力由后续里程碑承接。

## 6. API 契约

### 6.1 权威来源（接真实接口前必读）

| 优先级 | 文档 | 用途 |
| --- | --- | --- |
| 1 | [`location/backend/app/api/DEV.md` §4.2](../backend/app/api/DEV.md) | 全接口路径、请求体、`data` 字段、错误码（人类可读） |
| 2 | `http://localhost:8000/docs` | OpenAPI：`ApiResponse[XxxData]` 与各 `*Data` 强类型 |
| 3 | `location/backend/app/schemas/` | 字段细查（`response.py`、`log.py`、`report.py` 等） |

后端契约变更时，以 §4.2 为准；本文档只记录前端侧用法与示例。

### 6.2 统一响应信封

自 2026-06-23 起，所有 `/api/v1/*` 业务接口返回：

```jsonc
{ "ok": true,  "data": { ... }, "error": null }
{ "ok": false, "data": null 或降级数据, "error": { "code": "...", "message": "..." } }
```

**前端解包**：`src/api/request.js` 响应拦截器已处理信封——成功时 `res.data` 直接是业务负载；`ok===false` 时 Promise reject，`catch` 中可读 `error.error.code` / `error.error.message`。页面与 wrapper **不要**再读顶层 `ok` / `error`。

例外：请求体验证失败返回 HTTP `422`，body 为 `{ detail: [...] }`，不走业务信封。

常见错误码（`ApiCode`）：`es_unavailable`、`query_failed`、`invalid_param`、`not_found`、`graph_failed`。

### 6.3 环境与 baseURL

`.env.development` 当前配置：

```text
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_KIBANA_URL=http://localhost:5601
```

wrapper 内路径不含 `/api/v1` 前缀（由 baseURL 拼接）。

### 6.4 接口一览（解包后 `res.data` 形态）

| 方法 | wrapper（`src/api/`） | 路径 | 解包后 `data` 关键字段 |
| --- | --- | --- | --- |
| GET | `getApiHealth()` | `/health` | `{ status: "ok" }` |
| GET | `getSystemStatus()` | `/system/status` | `{ kafka_bootstrap_servers, kafka_topic, elasticsearch_hosts, elasticsearch_index_pattern, kafka, elasticsearch, docker, containers, services }` |
| GET | — | `/system/containers` | `{ project, available, error, containers }` |
| POST | `verifyPipeline()` | `/system/pipeline/verify` | `PipelineVerifyResponse`（`success`, `nodes`, `stdout`, `stderr` 等） |
| POST | `searchLogs()` | `/logs/search` | `{ items[], total, page, page_size, has_more, took_ms }` |
| GET | `getLogFields()` | `/logs/fields?log_type=` | 无参：`{ registered_log_types[] }`；有参：`{ log_type, catalog }` |
| POST | — | `/logs/aggregate` | `{ group_by, interval, buckets[], took_ms, extra? }` |
| POST | `diagnosis` 相关 | `/diagnosis` | `{ message, input, diagnosis{ anomaly_type, severity, root_cause, suggestion[], evidence_logs[], context_summary } }` |
| GET | `reports` 相关 | `/reports/recent` | `{ items[], total, limit }` |
| GET | — | `/reports/{id}` | `{ report_id, report }`（未命中 `report: null`，仍 `ok: true`） |
| GET | `getActiveAlerts()` | `/alerts/active` | `{ items[], total }` |
| POST | `acknowledgeAlert()` | `/alerts/{id}/ack` | `{ alert_id, status }` |
| GET | — | `/analysis/runs/recent` | `{ items[{ report_id, node_trace[], node_count, total_duration_ms, ... }], total, limit }` |
| POST | — | `/analysis/run` | `{ report_id, alert_id, node_trace[], alert_decision, errors[] }` |

### 6.5 系统运维页当前用法（F1 占位态）

F1 阶段系统运维已拆为三页，均为占位编排，真实数据与旧页能力迁移留待 **F3**：

| 页面 | 路径 | F1 状态 | 计划接入 |
| --- | --- | --- | --- |
| 链路健康与验证 | `/system/pipeline` | 占位（PipelineGraph + VerifyOutputPanel 空态） | F3：`verifyPipeline()` |
| 组件运行状态 | `/system/components` | 占位（StatusCard 矩阵） | F3：`getSystemStatus()`，迁移旧 `index.vue` |
| 配置快照 | `/system/config` | 占位（ConfigSnapshotCard 空态） | F3：`getSystemStatus()` 配置字段 |

**遗留完整实现**（未挂新路由，F3 迁移参考）：`src/views/system/index.vue` 仍保留旧版系统状态页，曾请求：

| 方法 | API wrapper | 实际路径 | 解包后用途 |
| --- | --- | --- | --- |
| GET | `getApiHealth()` | `/health` | `res.data.status` 探活 |
| GET | `getSystemStatus()` | `/system/status` | `res.data` 含 Kafka/ES/Docker 快照与 `containers` |
| POST | `verifyPipeline()` | `/system/pipeline/verify` | `res.data` 为验证结果（节点状态与终端输出） |

`/temp/developer` 在 F1 复用 `components.vue`（占位），不再直接挂载旧 `index.vue`。

## 7. 系统状态展示规则（遗留页 + F3 目标）

### 7.1 F1 现状

- 新路由下三页均为 `EmptyState` / 占位卡片，标注 `pending-api` 或阶段说明。
- 旧 `src/views/system/index.vue` 保留文件，含完整 Kafka/ES/Docker 展示与全链路验证逻辑，**当前不被侧边栏或 `/temp/developer` 引用**。

### 7.2 F3 迁移目标（旧 `index.vue` 行为基线）

迁移至 `pipeline` / `components` / `config` 后应保留以下规则（源自旧实现）：

- 复用 `src/components/system/ServiceStatusCard.vue` 与 `src/utils/systemStatus.js`。
- 展示 Frontend、Backend、Kafka、Elasticsearch、Logstash、Kibana 服务卡与配置快照。
- 全链路验证：触发后端 `verify_log_pipeline_full`，展示四节点状态与终端输出。
- 兜底：优先结构化字段；`kafka`/`elasticsearch` 缺失时用 `containers`/`services`/`docker.containers`；ES health `unknown` 时容器 `running` 兜底。
- 禁止退回「按钮 + raw JSON `<pre>`」调试页。

## 8. 本地启动与验证

安装依赖：

```powershell
cd C:\Users\zhurunjie\Desktop\elk\location\frontend
npm install
```

启动开发服务：

```powershell
npm.cmd run dev -- --host 0.0.0.0 --port 5173
```

构建验证：

```powershell
npm.cmd run build
```

浏览器验证：

- 平台入口：`http://localhost:5173/`（重定向至 `/dashboard`）
- 驾驶舱：`http://localhost:5173/dashboard`
- 监控示例：`http://localhost:5173/monitor/application`
- 分析示例：`http://localhost:5173/analysis/diagnosis`
- 系统运维：`http://localhost:5173/system/components`
- 开发者入口：`http://localhost:5173/temp/developer`（复用组件运行状态占位页）

F1 验收（构建 + 可导航）：

- `npm run build` 通过（当前约 735 modules）。
- 侧边栏可导航全部 16 个页面，各页可见占位区块与 `meta.title` 标题。
- TopBar 时间窗预设、预警角标（`getActiveAlerts` 轮询）、PipelineHealthDot（`getSystemStatus` 轮询）已挂载。

旧系统状态页完整验证（需手动改路由或待 F3 迁移后）：

- 直接访问遗留 `index.vue` 不在 F1 路由内；F3 完成后在 `/system/components` 与 `/system/pipeline` 复现下列行为。
- Backend API 正常、Kafka/ES/Logstash/Kibana 服务卡展示容器状态。

## 9. 常见排错

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| 页面出现 `Network Error` | 后端未启动或 CORS 头缺失 | 用 curl 检查 `access-control-allow-origin` |
| 只显示前后端正常，Kafka/ES unknown | 后端 `/system/status` 缺少 `containers/services/docker` | 检查 8000 是否启动了旧后端 |
| `/temp/developer` 空白或仅占位 | F1 复用 `components.vue` 占位页 | 完整开发者面板待 F3 迁移；检查路由是否指向 `SystemComponents` |
| Kafka topic 不存在 | Kafka 正常但 `app-logs` topic 未创建 | 后端会显示 `configured_topic.exists=false` |
| ES cluster health unknown | Elasticsearch 认证未配置 | 页面用容器 running 兜底，错误作为详情展示 |

## 10. 当前状态表（F1 落地）

| 模块 | 当前状态 | 风险 | 说明 |
| --- | --- | --- | --- |
| 设计令牌 / 全局样式 | 可用 | 低 | `assets/styles/index.css` 语义色、栅格、动效令牌就位 |
| composables | 可用 | 低 | `useTimeRange` + `usePolling`；Layout `provideTimeRange` |
| 布局 shell | 可用 | 低 | 双栏 + SidebarTree + TopBar + PipelineHealthDot |
| 路由 | 可用 | 低 | 16 子路由 + 5 条旧路由重定向 + `/temp/developer` |
| 通用组件 `common/` | 可用 | 低 | EmptyState、StatCard、StatusCard、SeverityBadge、LogTable（占位表）、TimeAxis、StageRing |
| 图表封装 `charts/` | 可用 | 低 | BaseChart + 5 图表；页面传 data，不直接 `import echarts` |
| API wrapper | 可用 | 中 | 信封解包就位；`metrics`/`reports`/`alerts` 部分 `USE_MOCK`；**契约回补待 F1-18** |
| 总览驾驶舱 | 占位（待 F4/F6） | 低 | 五区块编排 + EmptyState / 空图表占位 |
| 日志监控（7 页） | 占位（待 F2/F4） | 中 | LogMonitorShell 三段式 + `logTypeMeta` 配置驱动 |
| 智能分析（5 页） | 占位（待 F5/F6/F7） | 中 | 分区编排 + Gauge/StageRing 占位；无对话框形态 |
| 系统运维（3 页） | 占位（待 F3） | 中 | pipeline/components/config 占位；旧 `index.vue` 能力未迁移 |

## 11. 开发约束

- 页面不得直接使用 `axios`/`fetch`，应通过 `src/api/*.js`。
- 前端不得直接访问 ES、Kafka、Docker API。
- **图表只进不出**：ECharts 实例只允许存在于 `components/common/charts/`；页面组件传 data/option，禁止页面级 `import echarts`。
- **新增依赖仅 ECharts 一项**；不引入 Pinia、大型 UI 组件库等。
- **占位须标注**：F1/F2 占位区块使用 `EmptyState` 并标明 `pending-api` 或阶段说明；mock 数据须可识别为「演示数据」，禁止冒充真实后端数据。
- 系统状态相关页面不能硬编码容器假数据，只能展示后端返回值（F3 接入后）。
- 新增页面须同步更新 `layout/menu.js`、`router/index.js` 与本文档路由表。
- 路由变更必须同步更新本文档。
- 每次修改后至少运行 `npm.cmd run build`。

## 12. 开发日志

| 日期 | 修改内容 | 涉及文件 | 结果 | 遗留问题 |
| --- | --- | --- | --- | --- |
| 2026-05-14 | 重建前端目录级 DEV 文档 | `frontend/DEV.md` | 清理过期 `/state/` 约定，记录当前路由、API、系统状态展示规则 | 后续页面增强需持续维护 |
| 2026-05-14 | 恢复系统状态页和 `/temp/developer` | `src/views/system/index.vue`、`src/router/index.js`、`src/api/system.js`、`src/utils/systemStatus.js` | `/temp/developer` 可展示 Kafka、ES、Logstash、Kibana 容器状态 | ES cluster health 认证后续处理 |
| 2026-05-18 | 系统状态页新增全链路快速检测面板 | `src/views/system/index.vue`、`src/api/system.js` | 可触发后端 pipeline verify，展示四节点状态与 `verify_log_pipeline_full` 输出 | 长耗时验证依赖后端接口与 Kafka/ELK 当前运行状态 |
| 2026-05-19 | 快速检测纳入多线程日志生成验证 | `src/views/system/index.vue` | 默认传 `workers=2`，覆盖多线程日志生产到 ES 命中的链路 | 后续可把 workers 暴露为页面参数 |
| 2026-06-23 | 对齐后端统一 API 信封 | `src/api/request.js`、`frontend/DEV.md` §6 | `request.js` 拦截器解包 `{ok,data,error}`；DEV §6 指向 `backend/app/api/DEV.md` §4.2 并补全接口一览 | TopBar 角标等页面字段待 F6-07；**api 层待 F1-18** |
| 2026-06-23 | job 文档与总体规划 API 契约二轮对齐 | `frontend/job/*`、`前端开发总体规划.md` §6/§7 | 消除 logs/trace、fields POST、M1 未就绪等文档偏差；各 STATUS 标明 F1-18 阻塞 | 代码侧仍须执行 F1-18 |
| 2026-06-23 | **F1 骨架重构落地** | `composables/`、`layout/`、`components/common/`（含 charts）、`views/dashboard|monitor|analysis|system/`、`router/index.js`、`frontend/DEV.md` | 16 路由可导航、`npm run build` 通过（735 modules）；双栏树状导航、时间窗/轮询、图表与通用件就位；业务页均为占位 | 真实数据 F2~F7；API 契约 F1-18；系统能力 F3 自旧 `index.vue` 迁移 |
