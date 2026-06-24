# Frontend DEV 文档

| 2026-06-24 | **异常诊断默认两阶段顺序执行** | `views/analysis/diagnosis.vue`、`frontend/DEV.md` | 诊断提交明确按顺序执行两阶段：先 `POST /diagnosis` 展示规则诊断、上下文证据、根因与建议，再自动触发 `POST /analysis/run` 补充 LangGraph 规则子图、`node_trace`、报告详情或 `alert_decision`；第二阶段运行期间保持状态栏提示和按钮禁用；单次诊断摘要不再使用后端占位 `message`，避免展示“LangChain/LangGraph 深度分析仍待接入” | 第二阶段仍依赖后端 `/analysis/run`、报告详情和 ES 写入状态；失败时保留第一阶段规则诊断结果并显示非阻断提示 |
| 2026-06-24 | **异常诊断证据时间线间距自适应** | `components/analysis-diagnosis/EvidenceTimeline.vue`、`frontend/DEV.md` | 修复证据日志时间戳密集时按真实时间比例映射导致节点全部挤在左侧的问题；现在先按 `sortKey/timestamp` 排序，再按蛇形路径的行槽位均匀铺点，每行最多 12 个节点，保持时间顺序同时自动拉开视觉距离 | 仅调整前端排布算法；不改变 `evidence_logs[]` 数据契约 |
| 2026-06-24 | **异常诊断证据蛇形时间线** | `components/analysis-diagnosis/EvidenceTimeline.vue`、`frontend/DEV.md` | 证据时间线改为从左上起始、横向到右侧后下弯反向、再向左横走并循环的蛇形单线；证据点按可解析时间戳映射到整条路径，缺少有效时间时按排序顺序等距分布；常态仅显示圆点，hover/focus 时通过信息浮层展示时间、服务、摘要和详情；`npm.cmd run build` 通过 | 仅调整前端展示；证据数据仍来自 `evidence_logs[]`，浮层同时保留原生 `title` 兜底 |
| 2026-06-24 | **异常诊断单次诊断主路径修复** | `views/analysis/diagnosis.vue`、`frontend/DEV.md` | 修复单次诊断入口只走 `/analysis/run`、依赖规则子图/报告写入导致基础诊断不可用的问题；现在先调用稳定的 `submitDiagnosis()`/`POST /diagnosis` 展示单次规则诊断，再后台尝试 `/analysis/run` 补充 `node_trace` 与深度报告；`npm.cmd run build` 通过，后端诊断接口定向 pytest 通过 | 深度规则子图仍依赖 ES/报告链路；失败时页面保留单次诊断结论并显示非阻断提示 |
| 2026-06-24 | **异常诊断卡片位置与证据滚动修正** | `views/analysis/diagnosis.vue`、`frontend/DEV.md` | 将“单次诊断结果”与“处置建议”展示位置互换；证据时间线外层增加 320px 内部滚动容器和深色滚动条，避免证据节点过多时撑高整页；单次诊断结果在新右侧卡片中改为单列布局 | 仅调整前端布局，不改变诊断/分析 API 数据流 |
| 2026-06-24 | **异常诊断推理路径与建议结果拆分** | `components/analysis-diagnosis/SuggestionChecklist.vue`、`views/analysis/diagnosis.vue`、`frontend/DEV.md` | `SuggestionChecklist` 增加标题、建议清单、推理路径分区的显示开关；原“处置建议”卡片改名为“推理路径”且只显示 `node_trace` 推断图；“建议结果”移入“单次诊断结果”卡片内，复用原勾选清单逻辑 | 仅调整展示组合；建议数据仍来自 `diagnosis.suggestion[]` / `action_suggestions[]` |
| 2026-06-24 | **异常诊断推理图与证据路径去留白** | `components/analysis-diagnosis/LangGraphFlow.vue`、`SuggestionChecklist.vue`、`EvidenceTimeline.vue`、`views/analysis/diagnosis.vue`、`frontend/DEV.md` | 推理路径独立卡片启用 `LangGraphFlow` 填充模式：隐藏重复内标题、降低 fitView padding、放大节点并填满卡片；证据时间线改为类似推理路径的紧凑节点流，常态只显示时间/服务/摘要，hover 或键盘聚焦节点时显示详细信息 | 证据详情仍来自 `evidence_logs[]`；浏览器原生 `title` 同步保留，防止浮层被滚动区域裁切时不可读 |
| 2026-06-24 | **异常诊断证据时间线节点化修正** | `components/analysis-diagnosis/LangGraphFlow.vue`、`EvidenceTimeline.vue`、`frontend/DEV.md` | 推理路径填充模式恢复原始白色 UI，仅保留放大与低 padding 适配；证据时间线从网格卡片改为纵向“线 + 圆形节点 + 摘要”结构，hover/focus 节点显示详情浮层，强化时间线语义 | 证据区域仍保留内部滚动；详情浮层同时保留原生 `title` 兜底 |
| 2026-06-24 | **业务漏斗洞察文字对比度修正** | `components/analysis-funnel/LossLocator.vue`、`components/analysis-funnel/FunnelMain.vue`、`frontend/DEV.md` | 修复深色分析工作台中漏斗专属组件仍使用浅色主题变量导致文字与背景融合的问题；流失定位标题、当前步骤强文本、步骤标签、步骤元信息、按钮和演示标记统一改为低饱和高对比深色风格；`npm.cmd run build` 通过；浏览器验证关键文字颜色可读且无新 error | 后续新增漏斗组件应避免直接使用浅色全局 `--color-text/--color-surface` 变量 |

## 1. 文档用途

本文档是 `location/frontend/` 目录级维护基线，用于说明 Vue 前端当前真实状态、路由约定、API 契约、系统状态页展示规则和本地开发验证方式。后续修改前端代码时，应同步更新本文档。

## 2. 前端定位

前端是 ELK + Kafka + LangGraph 电商日志分析项目的展示层，职责包括：

- 展示总览驾驶舱、日志监控（7 类）、智能分析（5 类）、系统运维（3 类）共 16 个业务页面。
- 通过后端 API 获取日志、诊断结果、系统状态与聚合指标。
- 不直接访问 Elasticsearch、Kafka、Docker 或 Kibana API。
- 为开发/排查提供 `/temp/developer` 手动入口，复用「组件运行状态」页（与 `/system/components` 同视图）。

## 3. 技术栈

| 类别 | 当前选型 |
| --- | --- |
| 框架 | Vue 3 |
| 构建工具 | Vite |
| 路由 | vue-router |
| HTTP | axios |
| 图表 | ECharts 5（仅 `components/common/charts/` 内引用）+ `@vue-flow/core`（LangGraph 推断图）+ `@tsparticles/vue3`（粒子背板） |
| 默认端口 | 5173 |

## 4. 目录职责

| 路径 | 职责 |
| --- | --- |
| `src/api/` | API wrapper（7 个模块 + `request.js` + `metrics.js` 六模板），页面不得直接 `axios`/`fetch` |
| `src/composables/` | 跨页组合式逻辑：`useTimeRange`（全局时间窗）、`usePolling`（轮询）、`useLogQuery`（监控页日志查询状态机）、`useMetrics`（F4 六模板聚合查询与时间窗联动） |
| `src/views/dashboard/` | 总览驾驶舱页面 |
| `src/views/monitor/` | 日志监控 7 个子页（application、behavior、web-server 等） |
| `src/views/analysis/` | 智能分析 5 个子页（diagnosis、reports、alerts、trace、funnel） |
| `src/views/system/` | 系统运维 3 个子页（pipeline、components、config）；旧 `index.vue` 保留文件、已无路由引用 |
| `src/components/common/` | 通用展示件：EmptyState、StatCard（**F7-02** 环比 `delta` props）、**StatusCard**（F3 六组件矩阵）、SeverityBadge、LogTable（分页/排序/展开/链路跳转）、TimeAxis、StageRing、**ParticleBackdrop**（tsParticles 白名单背板） |
| `src/components/common/charts/` | ECharts 薄封装：BaseChart、TrendChart、BarChart、PieChart、GaugeChart、FunnelChart；统一读取 `utils/chartTheme.js` |
| `src/components/dashboard/` | 驾驶舱区块组件 |
| `src/components/monitor/` | 监控页壳层与筛选/图表带（LogMonitorShell 三段式编排、DynamicFilterBar 字段目录驱动筛选、ChartBand 配置驱动 2~3 图） |
| `src/components/analysis-diagnosis/` | 异常诊断中心专属：`DiagnosisEntryPanel`（活跃预警/时间窗上下文驱动）、`ConclusionPanel`、`EvidenceTimeline`、`ServiceTopology`、`SuggestionChecklist`、`LangGraphFlow`（`node_trace` → Vue Flow 推断图）、`DiagnosisStageRing`（报告页兼容复用） |
| `src/components/analysis-trace/` | 链路追踪专属：`TraceSearchBar`（检索 + localStorage 历史）、`TraceWaterfall`（CSS 泳道瀑布 + ERROR 着色 + 断点标记） |
| `src/components/analysis-reports/` | 周期报告专属：`ReportTimeline`、`ReportRiskPanel`、`ReportSections`（页脚 `DiagnosisStageRing`）、`RelationInsightCard`（**F7-01** 关系箭头卡 + 双迷你折线） |
| `src/components/analysis-alerts/` | 预警中心专属：`AlertBoard`（三态计数 + 24h 趋势）、`AlertTable`、`AlertDetailDrawer`（三段解释 + 诊断跳转） |
| `src/components/analysis-funnel/` | 业务漏斗专属组件 |
| `src/components/system/` | 系统运维区块（PipelineGraph、VerifyOutputPanel、ConfigSnapshotCard）；遗留 `ServiceStatusCard` 仅供旧 `index.vue` 只读参考 |
| `src/layout/` | 双栏布局壳：`index.vue` |
| `src/layout/menu.js` | 侧边栏树状目录唯一配置源（新增页面须同步改此文件与路由） |
| `src/layout/components/` | SidebarTree、SidebarTreeNode、TopBar、PipelineHealthDot |
| `src/router/` | 路由定义（16 子路由 + 旧路由重定向 + `/temp/developer`） |
| `src/utils/` | `format.js`（格式化）、`logTypeMeta.js`（监控页配置驱动）、`systemStatus.js`（F3 系统状态归一化与兜底，供三页与 PipelineHealthDot）、`kibanaLinks.js`（**F7-03** Discover/Dashboard 深链生成，不访问 Kibana API） |
| `src/assets/styles/` | 设计令牌与全局样式（`index.css`；**F7-04** `--transition-fast`/`--transition-chart`、`page-section` hover、`prefers-reduced-motion`） |

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
| POST | `searchLogs()` | `/logs/search` | `{ items[], total, page, page_size, has_more, took_ms }`（见 §6.6） |
| GET | `getLogFields()` | `/logs/fields?log_type=` | 无参：`{ registered_log_types[] }`；有参：`{ log_type, catalog }`（见 §6.6） |
| POST | — | `/logs/aggregate` | `{ group_by, interval, buckets[], took_ms, extra? }` |
| POST | `submitDiagnosis()`（`diagnosis.js`） | `/diagnosis` | `{ message, input, diagnosis{ anomaly_type, severity, route, root_cause, suggestion[], evidence_logs[], context_summary } }`（**不含** `node_trace`） |
| POST | `triggerAnalysisRun()`（`analysis.js`） | `/analysis/run` | `{ report_id, alert_id, node_trace[], alert_decision{}, errors[] }`（120s 超时；`graph_failed` 时 reject 但 `data.node_trace` 可降级读取） |
| GET | `getRecentAnalysisRuns()`（`analysis.js`） | `/analysis/runs/recent` | `{ items[{ report_id, node_trace[], node_count, total_duration_ms, ... }], total, limit }` |
| GET | `getRecentReports()`（`reports.js`） | `/reports/recent?limit=` | `{ items[{ report_id, report_type, title, risk_level, summary, created_at, task_id }], total, limit }` |
| GET | `getReportDetail()`（`reports.js`） | `/reports/{report_id}` | `{ report_id, report{ sections[], node_trace[], metrics_snapshot, degraded?, ... } }`（未命中 `report: null`，仍 `ok: true`） |
| GET | `getActiveAlerts()`（`alerts.js`） | `/alerts/active?limit=` | `{ items[{ alert_id, alert_type, severity, status, title, affected_service, evidence_count, created_at, updated_at, payload? }], total }` |
| POST | `acknowledgeAlert()`（`alerts.js`） | `/alerts/{alert_id}/ack` | `{ alert_id, status: 'acknowledged' }`（body 可选 `{ operator }`） |
| GET | `searchByTraceId()`（`logs.js`） | `/logs/search`（内部） | `{ items[], total, page, page_size, has_more, took_ms }`（`trace_id` + `page_size=500` + `sort_order=asc`） |

### 6.5 系统运维页（F3 落地）

系统运维三页均已对接真实 `system` API，数据经 `src/utils/systemStatus.js` 归一化，禁止硬编码容器假数据。

#### 6.5.1 三页路由与组件归属

| 页面 | 路径 | 视图 | 核心组件 | API wrapper | 刷新策略 |
| --- | --- | --- | --- | --- | --- |
| 链路健康与验证 | `/system/pipeline` | `views/system/pipeline.vue` | `PipelineGraph`、`VerifyOutputPanel` | `getSystemStatus()`、`verifyPipeline({ workers })` | `usePolling` 60s + 验证成功后重拉 status |
| 组件运行状态 | `/system/components` | `views/system/components.vue` | `StatusCard` × 6 | `getApiHealth()` + `getSystemStatus()` | mount + 60s 轮询 + 手动「刷新状态」 |
| 配置快照 | `/system/config` | `views/system/config.vue` | `ConfigSnapshotCard` | `getSystemStatus()` | mount 拉取；失败 EmptyState + 重试 |

| 入口 | 路径 | 说明 |
| --- | --- | --- |
| 侧边栏默认 | `/system/components` | 旧 `/system` 重定向至此 |
| 开发者入口 | `/temp/developer` | 复用 `components.vue`，与上表同数据源 |

#### 6.5.2 `system.js` 消费说明

| 方法 | 路径 | 解包后关键字段 | 消费方 |
| --- | --- | --- | --- |
| `getHealth()` / `getApiHealth()` | `/health` | `{ status: "ok" }` | `components.vue`（与 status 并行探活） |
| `getSystemStatus()` | `/system/status` | 顶层配置字段 + 嵌套 `kafka` / `elasticsearch` / `docker` / `containers` / `services` / `llm` | 三页 + `PipelineHealthDot`（`derivePipelineHealthTone`） |
| `getSystemContainers()` | `/system/containers` | `{ project, available, error, containers }` | 预留；三页当前不直接调用 |
| `verifyPipeline(payload)` | `/system/pipeline/verify` | `{ success, exit_code, duration_ms, nodes[], stdout, stderr, error? }` | `pipeline.vue` → `VerifyOutputPanel` |

**`verifyPipeline` 默认参数**（与旧 `index.vue`、后端 `PipelineVerifyRequest` 对齐）：`count=4`、`workers=2`（1~8）、`kafka_wait=45`、`es_wait=120`；请求超时 **210s**。

**禁止依赖**：顶层 `available` / `placeholder` / `overall` / `pipeline_healthy`（已废弃）；改读 `kafka.available`、`elasticsearch.available`、`docker.available` 及容器映射。

#### 6.5.3 各页数据映射

**`/system/pipeline`**

- `getSystemStatus()` → `getPipelineNodes(status)` → `PipelineGraph` 四节点（日志生产 → Kafka → Logstash → ES）。
- 用户触发验证 → `verifyPipeline({ workers })` → `VerifyOutputPanel` 展示 `nodes` / `stdout` / `stderr`；失败保留上次成功输出（若有）。
- status 拉取失败：`EmptyState` + 重试。

**`/system/components`**

- 并行 `getApiHealth()` + `getSystemStatus()` → `normalizeComponents(status, { apiHealth, frontendReady })` → 六卡矩阵：**Backend、Kafka、Elasticsearch、Logstash、Kibana、LLM**。
- 概览条：正常组件数 / 需关注组件数 / 最近刷新时间。
- ES 容器兜底激活时顶部展示 `fallback-banner`（见 §7.3）。
- 拉取失败：全卡 `offline` + 页顶 alert + 重试。

**`/system/config`**

- `getSystemStatus()` → `mapStatusToConfigGroups` → `ConfigSnapshotCard` 三组：**Kafka**（bootstrap_servers、topic）、**Elasticsearch**（hosts、index_pattern）、**LLM**（provider、model、api_key 脱敏）。
- 字段多级候选均无有效值时展示 **「未配置」**（非空字符串占位）。
- Kibana 外链：`import.meta.env.VITE_KIBANA_URL`（与 `.env.development` 一致）。
- 拉取失败：`EmptyState` + 重试。

#### 6.5.4 旧 `views/system/index.vue` 迁移说明

| 旧页能力 | 迁移目标 | 说明 |
| --- | --- | --- |
| 六服务状态卡（`ServiceStatusCard`） | `/system/components` | 改用 `common/StatusCard` + `normalizeComponents`；逻辑对齐 DEV §7.3 |
| 全链路验证面板 | `/system/pipeline` | `VerifyOutputPanel` + `verifyPipeline` |
| Kafka/ES 配置展示 | `/system/config` | `ConfigSnapshotCard` + status 字段映射 |
| `/temp/developer` 独立开发者页 | `/temp/developer` | **不再挂载** `index.vue`；复用 `components.vue` |

**文件处置**：`src/views/system/index.vue` 与 `components/system/ServiceStatusCard.vue` **保留于仓库**，供行为对照与历史 diff；**无任何路由引用**，请勿在新功能中扩展。新开发以三子页 + `systemStatus.js` 为准。

### 6.6 日志监控页当前用法（F2 落地）

7 个监控子页经 `LogMonitorShell` 统一编排，数据均走后端日志 API，不直连 ES。

**`searchLogs`（`POST /logs/search`）**

| 消费方 | 调用路径 | 请求要点 | 解包后用途 |
| --- | --- | --- | --- |
| `useLogQuery(logType)` | `composables/useLogQuery.js` | `log_types: [logType]`、`start_time`/`end_time`（来自 TopBar `useTimeRange`，ISO-8601 UTC）、`page`/`page_size`、`sort_by`（UI `@timestamp` 映射为 `timestamp`）、`sort_order`、`keyword`、DynamicFilterBar 合并的 terms/range 字段 | `items` → LogTable；`total` → 分页；`loading`/`error`/`errorCode` 驱动空态与重试 |
| `searchByTraceId(traceId)` | `api/logs.js`（预留） | 内部 `searchLogs`，`page_size=500`、`sort_order=asc` | 智能分析「调用链路追踪」F5 接入 |

`buildLogQueryPayload` 负责归一化分页默认值（`page=1`、`page_size=20`、`sort_by=timestamp`、`sort_order=desc`）及遗留 `time_range` → `start_time`/`end_time` 映射。失败时 `catch (e)` 可读 `e.error?.code`（如 `es_unavailable`、`query_failed`）。

**`getLogFields`（`GET /logs/fields?log_type=`）**

| 消费方 | 调用时机 | 解包后用途 |
| --- | --- | --- |
| `DynamicFilterBar` | 挂载时按子页 `logType` 请求 | `catalog.filter_fields` 驱动动态筛选项（terms / range / keyword）；目录失败或为空时回退 `logTypeMeta.fallbackFilters`，并标注「字段目录兜底」 |
| — | 无参调用（工具/调试） | `registered_log_types[]` 枚举已注册日志大类 |

**图表带（F4 已落地）**：`ChartBand` 读取各子页 `logTypeMeta.chartTemplates`（2~3 项），每项经 `useMetrics` 调用 `metrics.js` 对应模板 → `aggregateLogs`（`POST /logs/aggregate`）。`chartType` 映射 `TrendChart` / `BarChart` / `PieChart`；`options`（`group_by`、`top_n`、`interval`、`metric`）经 `extraFilters` 并入请求体，`LogMonitorShell` 已向 `ChartBand` 传入当前 `logType`，聚合锁定子页日志大类。加载失败单图 `EmptyState` + 重试；`metrics.USE_MOCK === true` 时角标「演示数据」。

**页面装配**：各 `views/monitor/*.vue` 仅 `getLogTypeMeta(key)` + `<LogMonitorShell>`，无重复查询逻辑；`trace_id` 列点击跳转 `/analysis/trace?trace_id=`。

### 6.7 F4 聚合指标：`metrics.js` 六模板与 `USE_MOCK`

图表线统一经 `src/api/metrics.js` 封装 `POST /logs/aggregate`（底层 `aggregateLogs`），页面与组件通过 `useMetrics` 消费，禁止页面直调 `aggregateLogs`。

#### 6.7.1 六模板一览

| 模板键（`useMetrics.template`） | wrapper 函数 | 默认 `log_types` | 默认 `group_by` | 默认 `interval` | 典型消费方 |
| --- | --- | --- | --- | --- | --- |
| `traffic` | `queryTraffic` | `application`, `web_server` | `service_name` | `1m` | 驾驶舱流量趋势、监控 URI/行为 Top N |
| `errors` | `queryErrors` | `application`, `web_server` | `error_code` | — | 驾驶舱错误分布、监控错误/状态码图、漏斗流失定位 |
| `latency` | `queryLatency` | `application`, `web_server`, `performance` | `service_name` | — | 驾驶舱耗时、监控慢接口/p95 |
| `behavior_funnel` | `queryBehaviorFunnel` | `behavior` | `event_type` | — | 漏斗主图、行为转化步骤 |
| `security` | `querySecurity` | `security` | `event_type` | — | 安全日志图表带 |
| `infra_health` | `queryInfraHealth` | `infrastructure`, `performance` | `service_name` | — | 性能/基础设施图表带 |

`useMetrics` 额外参数：

- `logType`：若传入，覆盖模板默认 `log_types` 为 `[logType]`（`ChartBand` 与 `LogMonitorShell` 已接通）。
- `extraFilters`：合并进请求体（`group_by`、`top_n`、`interval`、`metric` 等），用于 `logTypeMeta.chartTemplates[].options` 差异化。
- `range`：来自 `useTimeRange()`，`start_time`/`end_time` ISO-8601 UTC；变更 debounce **300ms** 后自动 `refresh`。
- 返回：`{ data, loading, error, refresh, isMock }`；`data` 为解包后 `{ group_by, buckets[], took_ms, interval?, extra? }`。

#### 6.7.2 `USE_MOCK` 切换策略（F4 范围）

| 模块 | 文件 | 当前默认值 | mock 形态 | UI 约定 |
| --- | --- | --- | --- | --- |
| 聚合指标 | `api/metrics.js` | **`USE_MOCK = false`** | `{ group_by, buckets: [], took_ms: 0 }`（无 `series`/`total` 自创字段） | `useMetrics.isMock` → 区块角标「演示数据」；空 buckets 走图表 placeholder |
| 周期报告 | `api/reports.js` | **`USE_MOCK = false`**（F6-01） | `{ items: [], total: 0, limit }` / 详情 `{ report_id, report: null }` | `reports.vue` 在 `USE_MOCK===true` 时页顶「演示数据」；驾驶舱 `LatestReportCard` 空列表走 EmptyState |
| 活跃预警 | `api/alerts.js` | **`USE_MOCK = false`**（F6-02） | `{ items: [], total: 0 }` / ack `{ alert_id, status }` | TopBar 角标读 `data.total`；`AlertDigest` 空列表走 EmptyState，无演示角标 |
| 规则诊断 | `api/diagnosis.js` | **`USE_MOCK = false`** | 完整 `MOCK_DIAGNOSIS_DATA`（含 `route: 'rule'`） | 离线演示时临时切 true |
| 智能分析运行 | `api/analysis.js` | **`USE_MOCK = false`** | `node_trace` 摘要 + `alert_decision` 即时诊断兜底 + `getRecentAnalysisRuns` 列表 | 离线演示时临时切 true |
| 日志明细 | `api/logs.js` | 无 mock | 真实 `searchLogs` / `aggregateLogs` | — |
| 系统状态 | `api/system.js` | 无 mock | 真实接口 | — |

**离线调试**：将 `metrics.js` 内 `USE_MOCK` 临时改为 `true`，无需改页面；图表带与驾驶舱 metrics 区块须展示「演示数据」角标。后端 M1 `/logs/aggregate` 已落地，**生产联调保持 `false`**。

**禁止**：仅关闭 `USE_MOCK` 而不对齐 mock 返回形态与页面字段读取（见 `job/API_CONTRACT.md` §5）。

### 6.8 总览驾驶舱数据源（F4 落地）

路径 `/dashboard`，视图 `views/dashboard/index.vue`，五区块自上而下：

| 区块 | 组件 | 数据来源 | API / 模板 | 刷新 |
| --- | --- | --- | --- | --- |
| 健康总仪表 + 核心指标带 | `HealthOverview` | 前端折算健康分 + 三模板聚合 | `useMetrics('traffic'/'errors'/'latency')`；`getSystemStatus()` → `derivePipelineHealthTone` | 时间窗 debounce；pipeline tone mount 拉取 |
| 流量趋势 + 错误分布 | `TrafficErrorPanel` | 双模板并行 | `traffic`（combo 面积+柱）；`errors`（横向条形 Top 服务 + 环形 error_code） | 时间窗联动 |
| 耗时分布 | `LatencyPanel` | 单模板 | `latency`（avg/p95/p99 多系列折线，读 `bucket.extra` / `extra.global_percentiles`） | 时间窗联动 |
| 活跃预警摘要 | `AlertDigest` | 真实预警 API | `getActiveAlerts({ limit: 5 })`（F6-07）；空列表 EmptyState + 跳转预警中心 | `usePolling` 30s |
| 最新体检结论 | `LatestReportCard` | 真实报告 API | `getRecentReports({ limit: 1 })`（F6-07）；`items[0]` 展示 `risk_level` + `summary`；空列表 EmptyState | mount 拉取 |

**健康分权重（前端）**：错误率 40% + 链路四态 30% + 活跃预警 30%。`HealthOverview` 内活跃预警 StatCard 仍为 **`ACTIVE_ALERTS_PLACEHOLDER = 0`**（TopBar/摘要已接真实 API，健康分权重项待后续小改）。`StatCard` 已支持 **`delta` / `deltaDirection` / `deltaKind`（F7-02）**，未传则不渲染环比箭头；`HealthOverview` 尚未传入对比数据。

### 6.9 监控图表带 `ChartBand` 数据源（F4 落地）

配置源：`utils/logTypeMeta.js` 各子页 `chartTemplates[]`（与总体规划 §3.2 表对齐）。每项结构：

```js
{ id, template, title, chartType: 'trend'|'bar'|'pie', options?: { group_by, top_n, interval, metric, switchable } }
```

| 子页 `logType` | 图表数 | 模板组合（`template` 键） |
| --- | --- | --- |
| `application` | 3 | errors 趋势、latency Top N、errors 饼图（error_code） |
| `behavior` | 3 | traffic（action 分布）、behavior_funnel、traffic（product Top N） |
| `web_server` | 3 | errors（status_code）、latency 趋势、traffic（URI Top N） |
| `performance` | 2 | infra_health 指标趋势、latency p95 对比 |
| `security` | 3 | security（risk_level / client_ip / 趋势） |
| `infrastructure` | 3 | infra_health（component / kafka_lag / resource_usage） |
| `audit` | 2 | traffic（operator Top N、action 分布） |

渲染：`ChartBand` → `ChartBandItem` × N → `useMetrics({ template, logType?, extraFilters })` → `resolveChartProps` → `common/charts/*`。`pickBuckets` 支持 `extra.by_status_code` / `extra.by_client_ip` 子桶。

### 6.10 业务漏斗页数据源（F4 落地）

路径 `/analysis/funnel`，视图 `views/analysis/funnel.vue`（注入 `useTimeRange`）。

| 区块 | 组件 | 数据来源 | 说明 |
| --- | --- | --- | --- |
| 主漏斗 | `FunnelMain` | `useMetrics({ template: 'behavior_funnel' })` | 五步 `event_type`：page_view → product_click → add_to_cart → checkout_click → pay_button_click；步骤转化率/流失率阈值着色；可点选步骤 |
| 流失定位 | `LossLocator` | `useMetrics({ template: 'errors', extraFilters: { top_n: 10 }, immediate: false })` | 选中步骤后 refresh；横向条形 Top 错误码；「查看应用日志」跳转 `/monitor/application?log_levels=ERROR&funnel_step=…&error_codes=…` |

**时段对比（F7-02）**：`funnel.vue` 已编排「主漏斗 / 时段对比」双 tab 与双 `FunnelChart` 并排（当前窗 vs 上一等长窗口）；常量 **`COMPARE_TAB_READY = false`** 时 tab 隐藏、仅展示主漏斗。后端对比 API / `es_compare_time_windows` 就绪后改为 `true` 即可启用。监控页尚未解析 URL `query` 预置筛选（跳转仅保留约定 query，F2 Shell 待增强）。

### 6.11 与总体规划差异记录（F4 图表线）

对照 `前端开发总体规划.md` §3.1 / §3.2 / §3.7，当前实现差异如下（非 bug 清单，供 F5/F6/F7 接续）：

| 章节 | 总体规划要求 | 当前实现 | 计划里程碑 |
| --- | --- | --- | --- |
| §3.1 核心指标带 | 5 卡含环比箭头 | 5 卡已接聚合；**StatCard 环比 props 已就绪（F7-02）**；`HealthOverview` **未传** `delta` | 后端对比数据就绪后 HealthOverview 传参 |
| §3.1 活跃预警数（健康分权重） | 活跃预警数参与健康分 | TopBar/摘要已真实；`HealthOverview` StatCard 与权重项仍为 **占位 0** | 后续小改 HealthOverview |
| §3.1 预警/报告摘要 | 真实 active 预警与最近报告 | **F6 已落地**：`USE_MOCK=false`；驾驶舱无演示角标；空列表 EmptyState | — |
| §3.2 图表带 log_type | 各子页专属聚合 | `LogMonitorShell` 已传 `logType` 至 `ChartBand`；聚合按当前监控子页锁定 `log_types` | — |
| §3.2 筛选 query 深链 | 漏斗跳转带预置筛选 | LossLocator 已写 query 约定；**监控页未读** `route.query` | 监控增强 |
| §3.4 关系洞察 | relation_chain 箭头卡 | **F7-01 已落地** `RelationInsightCard`；`reports.vue` 已传入 `relations/relation_chain` | — |
| §3.7 时段对比 | 双漏斗并排 tab | **F7-02 编排就绪**；`COMPARE_TAB_READY=false` 隐藏 tab | 对比 API 就绪后改 `true` |
| §3.7 流失跳转 | 跳转应用日志并带筛选 | 路由 push 已实现；明细表筛选待监控页解析 query | 同上 |

其余：驾驶舱五区块编排、七类 chartTemplates、漏斗五步与流失条形图、时间窗联动、`USE_MOCK` 角标策略均与总体规划一致或已在上一表标明偏差。

### 6.12 异常诊断中心数据源（F5 落地）

路径 `/analysis/diagnosis`，视图 `views/analysis/diagnosis.vue`，四区网格布局（与总体规划 §3.3 对齐）：

```text
[输入区 280px]  DiagnosisEntryPanel — 活跃预警 / 路由上下文 / 时间窗驱动自动取证
[结论区]        ConclusionPanel — 双仪表先于文字 + 根因卡 + 降级角标
[证据区]        EvidenceTimeline + ServiceTopology（1:1 网格）
[建议区]        SuggestionChecklist — 可勾选清单 + LangGraphFlow
```

| 区块 | 组件 | 数据来源 | 说明 |
| --- | --- | --- | --- |
| 输入区 | `DiagnosisEntryPanel` | `route.query.alert_id` / `getActiveAlerts()` / 全局时间窗 | 无手工粘贴日志入口；选择活跃预警或路由上下文后组装 `DiagnosisRequest`，由后端按服务、严重度、时间窗自动取证 |
| 结论区 | `ConclusionPanel` | `submitDiagnosis()` → `data.diagnosis` | `severity`/`confidence` Gauge 先于文字；`root_cause` 版式化卡片；`route==='rule'|'rule_only'` → 降级角标「统计模式 / 规则判定」 |
| 证据区 | `EvidenceTimeline` | `diagnosis.evidence_logs[]` | 垂直时间轴；ERROR 节点红色 |
| 证据区 | `ServiceTopology` | `affected_services` + `context_summary.similar_errors` | 简化拓扑 + 同类错误迷你柱图 |
| 建议区 | `SuggestionChecklist` | `diagnosis.suggestion[]` + `nodeTrace` | 勾选仅前端状态；内嵌 `LangGraphFlow`，以 Vue Flow 展示五段智能推断链路 |

**提交流程**（`diagnosis.vue`）：

1. `DiagnosisEntryPanel` 基于选中的活跃预警、路由服务名与全局时间窗构造 payload；前端不再要求用户粘贴异常日志。
2. `handleSubmit(payload)` 先触发 `submitDiagnosis(payload)`（`POST /diagnosis`），立即用 `data.diagnosis` 渲染单次规则诊断结论；该路径不依赖 LangGraph、报告写入或 ES 可写状态。
3. 单次诊断成功后，页面后台调用 `triggerAnalysisRun({ trigger_type: 'rule', trigger_event, time_window })` 补充 `node_trace` 与深度报告；后台失败只写入非阻断提示，不清空单次诊断结论。
4. 深度结果优先读取 `getReportDetail(report_id).data.report`；若详情未命中或返回 `report:null`，立即用 `/analysis/run` 的 `alert_decision.alert_candidate` 与 `alert_decision.explanation` 归一化为诊断字段。
5. `node_trace` 来自 `/analysis/run`，规则子图节点经 `filterRuleSubgraphTrace` 过滤；`graph_failed` 时从 `e.response.data.data.node_trace` 降级，否则使用上下文取证/事件关联/根因推断/风险定级/结论成文五段兜底轨迹。
6. 全局 `errorMessage` + 重试（保留 `lastPayload`）；`diagnosis.js` 或 `analysis.js` `USE_MOCK===true` 时页顶「演示数据」角标。

**与总体规划差异**：`confidence` 在规则降级时由 `ConclusionPanel` 展示规则置信区间文案（非 LLM 百分数）；深度诊断入口（F6）可复用本页 `@submit` 契约。

### 6.13 调用链路追踪页数据源（F5 落地）

路径 `/analysis/trace`，视图 `views/analysis/trace.vue`；**无独立 trace API**，经 `logs.js` 封装。

| 区块 | 组件 | 数据来源 | 说明 |
| --- | --- | --- | --- |
| 检索区 | `TraceSearchBar` | 用户输入 / `route.query.trace_id` | `emit('search', traceId)`；`localStorage` 键 `elk.trace.recent_ids` 保留最近 10 条 |
| 瀑布区 | `TraceWaterfall` | `searchByTraceId(traceId)` → `items[]` | CSS 泳道（按 `service_name` 分 lane）；`@timestamp`/`duration_ms` 定位条；ERROR/WARN 语义色；首条 ERROR 为断点标记 |

**`searchByTraceId`（`api/logs.js`）**：内部 `searchLogs({ trace_id, page: 1, page_size: 500, sort_by: 'timestamp', sort_order: 'asc' })`。

**页面行为**：

- `onMounted` + `watch(route.query.trace_id)`：有 query 时自动检索。
- 空结果：文案「未找到 trace_id…」；`es_unavailable`：专用错误文案 + 重试。
- 监控页 `LogTable` `trace_id` 列跳转 `/analysis/trace?trace_id=`（F2 已落地）。

### 6.14 `node_trace` → `LangGraphFlow` / `DiagnosisStageRing` 映射约定

`LangGraphFlow.vue`（诊断页）与 `DiagnosisStageRing.vue`（报告页兼容）将后端 `node_trace[{ node_name, status, duration_ms, output_summary }]` 翻译为五个业务阶段，**禁止在 UI 展示原始 `node_name`**。

| 业务阶段（`BUSINESS_STAGES`） | 索引 | 典型 `node_name` 映射 |
| --- | --- | --- |
| 取上下文 | 0 | `log_fetch`、`fetch_context`、`build_state`、`sample_logs`、`plan_queries` 等 |
| 关联分析 | 1 | `pattern_detect`、`correlate_events`、`merge_result`、`analyze_relations` 等 |
| 根因推断 | 2 | `rule_diagnose`、`infer_root_cause` 等 |
| 定级 | 3 | `assess_severity`、`main_alert_decision` 等 |
| 成文 | 4 | `report_write`、`generate_event_report`、`main_persist_result` 等 |

**规则**：

1. **显式表** `NODE_STAGE_MAP` 优先；未命中时用关键词启发式（`fetch|log`→0、`correlat|pattern`→1 等）。
2. **忽略节点**：`run_scheduled_subgraph`、`run_rule_subgraph`（子图容器，不映射到阶段）。
3. **同阶段多节点**：`status` 按 `failed > running > pending > skipped > success` 合并；`duration_ms` 累加。
4. **降级**（`degraded===true`，即 `diagnosis.route` 为 `rule`/`rule_only`）：索引 1/2/3 为 LLM 阶段——无节点或仍为 `pending` 时标「已跳过」；规则成功完成的 LLM 阶段耗时后缀「· 降级」。
5. **展示状态**：`success→done`、`failed→error`、`running→running`；展示文案为阶段中文名 + 耗时，非函数名。

数据来源分工：`POST /diagnosis` 是单次诊断主路径，**不返回** `node_trace`；诊断页推断图数据来自后台 `triggerAnalysisRun`，深度结论优先来自报告详情、兜底来自同次运行的 `alert_decision`，报告页阶段环数据来自 `getReportDetail.report.node_trace`。

### 6.15 智能体展示耦合规范落地（总体规划 §5）

F5 诊断中心与链路页对总体规划 §5 的落实记录（后续 F6 报告/预警页须同样遵守）：

| §5 规则 | F5 落实情况 |
| --- | --- |
| 1. 不设独立智能体页面 | 目录树无 Agent/调度节点；诊断结论仅在 `/analysis/diagnosis` 露出 |
| 2. 禁止对话框式输出 | 根因经 `ConclusionPanel` 固定版式卡；建议为核对清单；**无**聊天气泡/消息流/打字机 |
| 3. 数值先于文字 | `ConclusionPanel` 先渲染 severity/confidence Gauge，再展示 `anomaly_type` 徽章与根因正文 |
| 4. 调度过程 → 业务进度 | 诊断页用 `LangGraphFlow` 展示五阶段中文推断图，报告页保留 `DiagnosisStageRing`；`node_name` 不暴露给用户 |
| 5. 降级可感知但不突兀 | `route==='rule'` → 结论卡灰色角标 + 阶段环「统计模式 · 部分 LLM 阶段已跳过」；不弹窗 |
| 6. 图表对齐后端聚合 | 链路页仅展示 `searchLogs` 明细；拓扑/迷你柱图为 props 驱动轻量展示，无浏览器端大规模聚合 |

### 6.16 周期体检报告页数据源（F6 落地）

路径 `/analysis/reports`，视图 `views/analysis/reports.vue`，左右双栏（与总体规划 §3.4 对齐）：

```text
[左栏]  ReportTimeline — 最近报告时间轴，可选中
[右栏]  ReportRiskPanel — 风险仪表 + 定级理由
        ReportSections — 三节要点 + 页脚 DiagnosisStageRing
        RelationInsightCard — 关联洞察（**F7-01**）
```

| 区块 | 组件 | 数据来源 | 说明 |
| --- | --- | --- | --- |
| 时间轴 | `ReportTimeline` | `getRecentReports({ limit: 20 })` → `data.items` | mount 拉列表；按 `created_at` 默认选中最新；loading/error/retry |
| 风险定级 | `ReportRiskPanel` | `getReportDetail(id)` → `data.report` | Gauge 展示 `risk_level`；`risk_reason` / `summary` 文案；`degraded` → 统计模式角标 |
| 报告拆解 | `ReportSections` | 同上 `report.sections[]` | 固定三节标题「总体结论 / 异常发现 / 业务洞察」；要点列表；页脚 `node_trace` → `DiagnosisStageRing`（映射见 §6.14） |
| 关联洞察 | `RelationInsightCard` | `report.relations` / `relation_chain`（**F7-01**） | 左指标 → 右指标箭头卡 + 双 `TrendChart` 迷你折线；`confidence` 脚注；无有效数据 `v-if` 不占位；`USE_MOCK` 且无 relations 时展示 `DEMO_RELATIONS` + 角标「演示数据」 |

**接线状态**：`reports.vue` 已向 `RelationInsightCard` 传入 `relations/relation_chain`；非 mock 路径仅展示后端真实 relation_chain，空数据不占位。

**页面行为**：

- `onMounted` → `loadRecentReports` → 有项则 `pickLatestReportId` + `loadReportDetail`。
- 时间轴 `@select` 切换详情；列表/详情失败分别展示错误条 + 重试。
- 全空列表：`EmptyState`「暂无周期报告」；`report: null` 时详情区提示「报告详情为空或已过期」。
- `reports.js` `USE_MOCK===true` 时页顶「演示数据」角标（默认 false）。

### 6.17 预警中心页数据源（F6 落地）

路径 `/analysis/alerts`，视图 `views/analysis/alerts.vue`，三段纵向编排（与总体规划 §3.5 对齐）：

| 区块 | 组件 | 数据来源 | 说明 |
| --- | --- | --- | --- |
| 状态看板 | `AlertBoard` | `getActiveAlerts({ limit: 50 })` 派生 | `boardCounts`：`active=total`、本页 ack 会话计数 + 列表内 `acknowledged`/`resolved`；24h 趋势由 `created_at` 按小时分桶（无数据时不画趋势） |
| 预警列表 | `AlertTable` | 同上 `data.items` / `data.total` | 列：严重度、类型、服务、证据数、时间、操作；`@ack` → `acknowledgeAlert`；选中行高亮 |
| 详情抽屉 | `AlertDetailDrawer` | 选中行 + `payload` 解析 | 三段解释（现象/影响/建议）来自 `payload.explanation` 或扁平字段；证据 `payload.evidences`；关联报告链至 `/analysis/reports`；`@diagnose` → `/analysis/diagnosis?alert_id=` |

**页面行为**：

- mount `loadAlerts`；**30s 静默轮询** `loadAlerts({ silent: true })`（与 TopBar 同周期，ack 后下次轮询更新角标）。
- `handleAck`：成功后 `sessionAckCount++`、关闭抽屉、`loadAlerts({ silent: true })`。
- 列表失败：`AlertTable` error + 重试；抽屉关闭时 `selectedAlert` 清空。
- 诊断入口：`DiagnosisEntryPanel`（F5）同样消费 `getActiveAlerts` 供「选择活跃预警」tab。

### 6.18 全局预警与摘要接线（F6-07 落地）

| 消费方 | 文件 | API | 字段与行为 |
| --- | --- | --- | --- |
| TopBar 角标 | `layout/components/TopBar.vue` | `getActiveAlerts()`（默认 limit 50） | `alertCount = data.total ?? data.items.length ?? 0`；`usePolling` **30s**；`>0` 红点 + 数字；点击跳转 `/analysis/alerts`；失败角标 **0** + `console.warn` 错误码 |
| 驾驶舱预警摘要 | `components/dashboard/AlertDigest.vue` | `getActiveAlerts({ limit: 5 })` | 前 5 条 `items`；`SeverityBadge` + 服务 + 时间；行点击/「查看全部」→ `/analysis/alerts`；`usePolling` 30s；**无**演示数据角标 |
| 驾驶舱最新报告 | `components/dashboard/LatestReportCard.vue` | `getRecentReports({ limit: 1 })` | `items[0]`：`risk_level` 语义色点 + `summary` + `report_type` 标签；点击 → `/analysis/reports`；mount 拉取；**无**演示兜底 |

**协调约定**：预警 ack 后不强制即时刷新 TopBar，依赖 30s 轮询（F6-07 验收口径）。`HealthOverview` 健康分内活跃预警权重仍占位，见 §6.8。

### 6.19 F7 增强与体验抛光（F7 落地）

F7 为前端里程碑收尾阶段，在 F1~F6 业务骨架与真实 API 基础上做关系洞察、双窗口对比预留、Kibana 深链工具、全站动效抛光与可选粒子背板。

#### 6.19.1 关系洞察卡（F7-01）

| 项 | 说明 |
| --- | --- |
| 组件 | `components/analysis-reports/RelationInsightCard.vue` |
| Props | `relations`（`relation_chain` 数组）、`visible`（默认 true） |
| 视觉 | 每条关系：描述文案 + 左/右指标名 + 箭头 + 两侧 `TrendChart`（高 88px）+ 可选 `confidence` |
| 降级 | `displayRelations` 为空时不渲染；`reports.js` `USE_MOCK===true` 且无 relations 时用内置 `DEMO_RELATIONS` 并标「演示数据」 |
| 消费 | `reports.vue` 报告拆解区；消费 `relations/relation_chain` 后展示后端数据（见 §6.16） |

#### 6.19.2 双窗口对比（F7-02）

| 项 | 说明 |
| --- | --- |
| StatCard | 新增 `delta`、`deltaDirection`（`up`/`down`/`flat`）、`deltaKind`（`ratio`/`percent`）；三者齐备且数值有效时才渲染环比行；格式化走 `format.js` |
| 漏斗页 | `funnel.vue` 常量 `COMPARE_TAB_READY`（默认 **false**）；为 true 时展示「主漏斗 / 时段对比」tab，对比窗为**上一等长窗口**，双 `FunnelChart` 并排；数据经 `queryBehaviorFunnel` 分别拉当前窗与 baseline |
| 驾驶舱 | `HealthOverview` 五张 StatCard **尚未**传入 `delta`；待后端 `es_compare_time_windows` 或 metrics 对比参数就绪 |

#### 6.19.3 Kibana 深链工具（F7-03）

| 函数 | 文件 | 行为 |
| --- | --- | --- |
| `getKibanaBaseUrl()` | `utils/kibanaLinks.js` | 读 `VITE_KIBANA_URL`，无则 `null` |
| `buildDiscoverLink({ index, query, timeRange })` | 同上 | Rison 拼装 Discover URL；时间窗最长 24h；缺 base/index/时间则 `null` |
| `buildDashboardLink(id)` | 同上 | Dashboard 查看页外链 |

`.env.example` 已文档化 `VITE_KIBANA_URL` 与可选 `VITE_KIBANA_DEFAULT_INDEX_PATTERN`。规则与后端 `kibana_generate_link` 对齐。**当前无页面 import**；`config.vue` 仍用 env 直链 Kibana 根 URL，监控页「在 Kibana 中打开」为扩展位。

#### 6.19.4 动效抛光（F7-04）

| 范围 | 实现 |
| --- | --- |
| `assets/styles/index.css` | `--transition-fast`（180ms）、`--transition-chart`（400ms）；`.page-section` hover 轻抬升 + 阴影；`@media (prefers-reduced-motion: reduce)` 全局减弱过渡 |
| `charts/BaseChart.vue` | `animationDuration` / `animationDurationUpdate` 统一 **400ms**；`prefers-reduced-motion` 时 `animation: false`；`setOption` 平滑更新 |

全站图表经 `BaseChart` 继承上述策略；业务页未改数据逻辑。

#### 6.19.5 粒子背板（F7-05，已启用）

| 项 | 说明 |
| --- | --- |
| 组件 | `ParticleBackdrop.vue`（基于 `@tsparticles/vue3` + `@tsparticles/slim`，统一粒子运动、密度与 reduce-motion 降级） |
| Props | `variant`（`dashboard`/`pipeline`/`diagnosis`）、`intensity`（0~1）、`accentColor`（可选） |
| 白名单挂载 | 每页 ≤1 处：`/dashboard` 英雄区（`intensity=0.55`）、`/system/pipeline` 图谱背板（验证时 intensity 0.4→0.7）、`/analysis/diagnosis` 结论区背板（severity 驱动 accent，≤15% 微调） |
| 降级 | `prefers-reduced-motion` → 静态渐变网格；`pointer-events: none`，`z-index: 0` |
| 验收 | P-01~P-07 已通过（见 `job/task_m7/STATUS.md` F7-05 行）；**未跳过** |

## 7. 系统状态展示规则（F3 已落地，与 `systemStatus.js` 对齐）

### 7.1 归一化入口

| 函数 | 用途 | 消费方 |
| --- | --- | --- |
| `normalizeComponents(status, options)` | 六组件统一结构 `{ key, label, status, detail, port?, container? }`；`status` 为 `healthy` / `degraded` / `down` / `unknown` / `offline` | `components.vue` |
| `getPipelineNodes(status)` | 四节点链路 `{ key, label, status, detail? }` | `pipeline.vue` → `PipelineGraph` |
| `derivePipelineHealthTone(status)` | 综合四态 `success` / `warning` / `danger` / `unknown` | `PipelineHealthDot`（TopBar） |
| `resolveSystemStatusError(error)` | 离线 / 超时 / 业务错误码与文案 | 三页错误态 |
| `getContainerEntry` / `resolveContainersMap` | 容器映射互备 | 上述函数内部 |

### 7.2 容器与嵌套字段兜底（强制）

1. **容器映射互备**：单组件状态优先 `status.containers[key]`，其次 `status.services[key]`，再次 `status.docker.containers[key]`（`getContainerEntry` / `resolveContainersMap`）。
2. **禁止读废弃顶层字段**：不使用 `overall`、`pipeline_healthy`、顶层 `available`；链路健康由 `derivePipelineHealthTone` 从 `kafka.available`、`elasticsearch.available`、`docker.available` 与容器 running 态折算。
3. **Elasticsearch 集群健康**：
   - `green` / `yellow` / `red` → 直接映射展示态（yellow → `degraded`）。
   - `cluster_status === 'unknown'` 且容器 `running` → 展示 `degraded`，详情「健康未知，按容器态展示」；`components.vue` 显示 `fallback-banner`。
4. **Kafka**：`kafka.available === true` 且容器 running → `healthy`；仅一侧可用 → `degraded`；双侧不可用 → `down`。
5. **Backend**：`system/status` 成功即标记 `backend_api_status: 'ok'`（页面层注入）；否则回退 `getApiHealth().status`。
6. **LLM**：读 `status.llm.available`；无字段 → `unknown`，详情「后端暂未返回 LLM 连通性状态」。
7. **配置缺失**：`config.vue` 字段无有效标量/数组 → 展示「未配置」，禁止伪造默认值。
8. **请求失败**：`normalizeComponents(null, { error })` 六卡均为 `offline`；禁止退回「按钮 + raw JSON `<pre>`」调试形态。

### 7.3 与旧 `index.vue` 的差异

- 新页使用 `components/common/StatusCard.vue`，旧页 `ServiceStatusCard` 仅作只读参考。
- 旧页含 Frontend 服务卡；新矩阵以 Backend 代表 API 侧，Frontend 由当前页面加载态隐含。
- `/temp/developer` 与 `/system/components` 同视图，不再提供旧页独立布局。

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
- 系统运维：`http://localhost:5173/system/components`（默认落地页）
- 链路验证：`http://localhost:5173/system/pipeline`
- 配置快照：`http://localhost:5173/system/config`
- 开发者入口：`http://localhost:5173/temp/developer`（复用组件运行状态页）

F1 验收（构建 + 可导航）：

- `npm run build` 通过（当前约 735 modules）。
- 侧边栏可导航全部 16 个页面，各页可见占位区块与 `meta.title` 标题。
- TopBar 时间窗预设、预警角标（`getActiveAlerts` 轮询）、PipelineHealthDot（`getSystemStatus` 轮询）已挂载。

F2 验收（监控线真实查询，需后端 8000 + ES 有数据）：

- 任选监控子页（如 `/monitor/application`）：DynamicFilterBar 加载字段目录或兜底筛选项；变更筛选/关键字/分页/排序后 LogTable 请求 `searchLogs` 并展示结果。
- 切换 TopBar 时间窗后列表自动重查（debounce ≤300ms）。
- `es_unavailable` 等错误时 LogTable 空态 + 重试按钮可用。
- ChartBand 已接 F4 聚合图表（见 §6.9）；F2 验收时若仅验证明细表可忽略图表数据。
- 7 子页结构一致，均由 `logTypeMeta` 配置驱动，无重复模板代码。

F3 验收（系统线真实状态，需后端 8000 + Docker 栈可选）：

- `/system/components`：六张 `StatusCard` 展示真实容器/嵌套字段；60s 自动刷新；手动刷新与错误重试可用；ES `unknown` 时可见兜底横幅。
- `/system/pipeline`：`PipelineGraph` 四节点随 status 着色；触发全链路验证后 `VerifyOutputPanel` 展示终端输出（默认 `workers=2`）；验证后图谱重拉。
- `/system/config`：Kafka / ES / LLM 三组配置；缺失项为「未配置」；`VITE_KIBANA_URL` 可外链 Kibana。
- TopBar `PipelineHealthDot` 与 `derivePipelineHealthTone` 一致，点击跳转系统运维。
- 旧 `views/system/index.vue` 无路由可达；能力已在三子页复现。

F4 验收（图表线聚合，需后端 8000 + ES 有聚合数据；离线可 `metrics.js` `USE_MOCK=true`）：

- `/dashboard`：`HealthOverview` Gauge + 五 StatCard 随时间窗刷新；`TrafficErrorPanel` 流量叠加与错误双图；`LatencyPanel` 耗时三系列；`AlertDigest`/`LatestReportCard` 可展示列表（mock 时见「演示数据」角标）。
- 任选监控子页（如 `/monitor/application`）：`ChartBand` 展示 2~3 张配置驱动图表；筛选/表格行为与 F2 一致；单图失败可重试。
- `/analysis/funnel`：主漏斗五步 + 转化率；选中步骤后 `LossLocator` 错误码横条；可跳转应用监控页。
- `metrics.USE_MOCK=false`（默认）时聚合走真实 `/logs/aggregate`；`true` 时 metrics 相关区块显示「演示数据」。
- `npm run build` 通过。

F5 验收（智能线诊断 + 链路，需后端 8000；诊断/分析 mock 可临时 `USE_MOCK=true`）：

- `/analysis/diagnosis`：活跃预警/路由上下文/时间窗驱动提交，无手工粘贴日志入口；`ConclusionPanel` 双仪表 + 根因卡；证据时间轴/拓扑随 `evidence_logs`/`affected_services` 更新；建议清单可勾选；`LangGraphFlow` 五阶段随 `triggerAnalysisRun` 的 `node_trace` 更新；规则降级角标可见；mock 时页顶「演示数据」。
- `/analysis/trace`：`?trace_id=` 自动检索；手动搜索 + 历史标签；`TraceWaterfall` 泳道与 ERROR 断点；空结果/`es_unavailable` 错误态 + 重试。
- 监控页 `trace_id` 点击可跳入 trace 页并自动检索。
- 全页无对话框式智能体输出；`npm run build` 通过。

F6 验收（结果线报告 + 预警 + 全局接线，需后端 8000 + M4/M5 报告/预警数据；离线可 `reports.js`/`alerts.js` `USE_MOCK=true`）：

- `/analysis/reports`：时间轴列表 + 默认选中最新；右栏风险仪表与三节拆解随 `getReportDetail` 联动；`node_trace` 页脚阶段环；全空 EmptyState；列表/详情错误重试。
- `/analysis/alerts`：看板三态计数 + 24h 趋势（有数据时）；表格 `getActiveAlerts` 驱动；ack 后列表刷新；抽屉三段解释 + 诊断跳转 `?alert_id=`；30s 静默轮询。
- `/dashboard`：`AlertDigest` / `LatestReportCard` 真实 API，无「演示数据」角标；空列表 EmptyState + 跳转链接。
- TopBar：`getActiveAlerts` 30s 轮询，`total` 驱动角标，点击跳转预警中心。
- `reports.js` / `alerts.js` 默认 **`USE_MOCK=false`**；mock 时 reports 页顶角标可见。
- `npm run build` 通过。

F7 验收（增强与体验抛光，可与 F6 并行验部分项）：

- `/analysis/reports`：`RelationInsightCard` 在 mock 或无 relations 时按 §6.19.1 降级；有 `relations` 时箭头卡 + 双迷你折线；无数据不占位。
- `StatCard`：传入 `delta`+`deltaDirection` 时显示环比箭头；未传则不显示（驾驶舱默认无箭头）。
- `/analysis/funnel`：`COMPARE_TAB_READY=false` 时仅主漏斗；改为 `true` 后时段对比 tab 与双漏斗可见（需 `queryBehaviorFunnel` 有数据）。
- `kibanaLinks.js`：`getKibanaBaseUrl` / `buildDiscoverLink` / `buildDashboardLink` 在 env 齐全时返回合法 URL，缺配置返回 `null`。
- 动效：图表数据刷新有过渡（约 400ms）；`.page-section` hover 一致；系统开启 `prefers-reduced-motion` 时图表无动画、卡片仅阴影。
- 粒子：`/dashboard`、`/system/pipeline`、`/analysis/diagnosis` 各 1 处背板；不挡点击；reduce-motion 为静态渐变。
- `npm run build` 通过。

## 9. 常见排错

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| 页面出现 `Network Error` | 后端未启动或 CORS 头缺失 | 用 curl 检查 `access-control-allow-origin` |
| 只显示前后端正常，Kafka/ES unknown | 后端 `/system/status` 缺少 `containers/services/docker` | 检查 8000 是否启动了旧后端 |
| `/temp/developer` 与 `/system/components` 不一致 | 路由应指向同一 `SystemComponents` 组件 | 检查 `router/index.js` 中 `/temp/developer` |
| ES 显示 degraded + 兜底横幅 | `cluster_status=unknown` 且容器 running | 符合 §7.2 规则；配置 ES 认证后可得 green/yellow/red |
| Kafka topic 不存在 | Kafka 正常但 `app-logs` topic 未创建 | 后端 `configured_topic.exists=false`；配置页 topic 可能为「未配置」 |
| 全链路验证超时 | 默认 210s；ES 索引慢 | 检查 `verifyPipeline` stderr；可调 `es_wait`（页面暂未暴露参数） |

## 10. 里程碑与模块状态（F1 ~ F7 落地）

### 10.1 里程碑总览

| 里程碑 | 主题 | 状态 | 核心交付 | 主要遗留 |
| --- | --- | --- | --- | --- |
| **F1** | 骨架与路由 | **已落地** | 16 子路由、双栏布局、`common/`+`charts/`、composables、占位业务页 | 真实数据；API 信封对齐 |
| **F2** | 监控线 | **已落地** | 7 类 `searchLogs`、`DynamicFilterBar`、`LogMonitorShell`、`LogTable` | 图表带待 F4 |
| **F3** | 系统线 | **已落地** | pipeline/components/config、`systemStatus.js`、六卡矩阵、链路验证 | verify 高级参数 UI；`getSystemContainers` 预留 |
| **F4** | 图表线 | **已落地** | `metrics.js` 六模板、`useMetrics`、驾驶舱五区块、`ChartBand`、漏斗主图 | 环比待 F7 |
| **F5** | 智能线 | **已落地** | 诊断四区、`LangGraphFlow`、`TraceWaterfall`、§5 耦合规范 | 依赖后端 `/analysis/run` 返回稳定 `node_trace` |
| **F6** | 结果线 | **已落地** | 报告/预警页、TopBar 角标、`AlertDigest`/`LatestReportCard` 真实 API | HealthOverview 活跃预警权重占位 |
| **F7** | 增强与收尾 | **已落地** | 关系洞察卡、StatCard 环比、漏斗对比 tab 编排、`kibanaLinks`、动效抛光、粒子背板 | 对比 API、`HealthOverview` delta、kibana 消费方 |

**前端七阶段（F1~F7）代码与文档基线已闭合**；后续为联调小改与后端字段对齐，不再新增里程碑编号。

### 10.2 模块状态表

| 模块 | 当前状态 | 风险 | 说明 |
| --- | --- | --- | --- |
| 设计令牌 / 全局样式 | **可用（F7-04）** | 低 | 语义色、栅格、动效令牌；`page-section` hover；`reduce-motion` 全局降级 |
| composables | 可用 | 低 | `useTimeRange` + `usePolling` + `useLogQuery` + **`useMetrics`**；Layout `provideTimeRange` |
| 布局 shell | 可用 | 低 | 双栏 + SidebarTree + TopBar + PipelineHealthDot |
| 路由 | 可用 | 低 | 16 子路由 + 5 条旧路由重定向 + `/temp/developer` |
| 通用组件 `common/` | **可用（F7-02/05）** | 低 | EmptyState、StatCard（环比 props）、StatusCard、SeverityBadge、LogTable、TimeAxis、StageRing、**ParticleBackdrop** |
| 图表封装 `charts/` | **可用（F7-04）** | 低 | BaseChart 400ms 过渡 + reduce-motion；Trend/Bar/Pie/Gauge/Funnel |
| `kibanaLinks.js` | **可用（F7-03）** | 低 | Discover/Dashboard 深链；**无页面消费** |
| API wrapper `logs.js` | 可用 | 中 | `searchLogs`/`getLogFields`/`aggregateLogs`/`searchByTraceId` 契约对齐后端 |
| API wrapper `metrics.js` | **可用** | 低 | 六模板 → `aggregateLogs`；**默认 `USE_MOCK=false`** |
| 监控筛选 `DynamicFilterBar` | 可用 | 中 | `getLogFields` 驱动；目录失败回退 `logTypeMeta.fallbackFilters` |
| 监控骨架 `LogMonitorShell` | 可用 | 低 | 筛选 + 图表带 + LogTable；`useLogQuery` 串联查询 |
| 监控图表带 `ChartBand` | **可用（F4）** | 中 | `chartTemplates` 配置驱动；`useMetrics` 并行；Shell 已传 `logType` prop |
| 总览驾驶舱 | **可用（F4+F6+F7-05）** | 中 | 五区块真实 metrics + 预警/报告 API；英雄区粒子背板；健康分活跃预警 StatCard 仍占位 0；StatCard 环比未传参 |
| 驾驶舱组件 `dashboard/` | **可用（F4+F6）** | 低 | HealthOverview、TrafficErrorPanel、LatencyPanel、AlertDigest、LatestReportCard |
| 日志监控（7 子页） | **可用（真实日志 + 图表）** | 中 | 明细 `searchLogs` + 图表带聚合；依赖后端 ES 数据 |
| 业务漏斗 `/analysis/funnel` | **可用（F4+F7-02）** | 中 | 主漏斗 + 流失定位；时段对比 tab 编排就绪（`COMPARE_TAB_READY=false`） |
| API wrapper `diagnosis.js` | **可用** | 中 | `submitDiagnosis` → `/diagnosis`；`USE_MOCK=false` |
| API wrapper `analysis.js` | **可用** | 低 | `triggerAnalysisRun`（120s 超时）、`getRecentAnalysisRuns`；`USE_MOCK=false` |
| 异常诊断 `/analysis/diagnosis` | **可用（F5+体验收口+联调修复）** | 低 | 上下文驱动诊断 + 结论区粒子背板 + `LangGraphFlow` 推断图；报告详情未命中时用 `alert_decision` 即时结果兜底 |
| 诊断组件 `analysis-diagnosis/` | **可用（F5+体验收口）** | 低 | Entry/Conclusion/Evidence/Topology/Suggestion + `LangGraphFlow`；`DiagnosisStageRing` 供报告页兼容 |
| 调用链路 `/analysis/trace` | **可用（F5）** | 中 | `searchByTraceId` + query 深链 + 泳道瀑布 |
| 链路组件 `analysis-trace/` | **可用（F5）** | 低 | `TraceSearchBar`（历史 localStorage）、`TraceWaterfall`（CSS 泳道） |
| API wrapper `reports.js` | **可用（F6）** | 低 | `getRecentReports`/`getReportDetail`；**`USE_MOCK=false`** |
| API wrapper `alerts.js` | **可用（F6）** | 低 | `getActiveAlerts`/`acknowledgeAlert`；**`USE_MOCK=false`** |
| 报告组件 `analysis-reports/` | **可用（F6+F7-01）** | 低 | Timeline/RiskPanel/Sections + 阶段环；**RelationInsightCard** 已实装 |
| 预警组件 `analysis-alerts/` | **可用（F6）** | 低 | Board/Table/Drawer props+emit 契约 |
| 周期报告 `/analysis/reports` | **可用（F6+F7-01）** | 中 | 双栏装配 + 列表/详情联动；已传入 `relations/relation_chain` |
| 预警中心 `/analysis/alerts` | **可用（F6）** | 中 | 看板+表+抽屉 + ack + 30s 轮询 + 诊断深链 |
| TopBar 预警角标 | **可用（F6-07）** | 低 | `getActiveAlerts` 30s 轮询 → `/analysis/alerts` |
| API wrapper `system.js` | **可用** | 低 | `getSystemStatus`/`verifyPipeline`/`getHealth` 契约注释对齐后端 |
| `systemStatus.js` 归一化 | 可用 | 低 | 六组件卡、四节点链路、PipelineHealthDot 四态；容器互备与 ES unknown 兜底 |
| 系统组件 `system/` | 可用 | 低 | PipelineGraph、VerifyOutputPanel、ConfigSnapshotCard 已装配三页 |
| 系统运维（3 页） | **可用（F3+F7-05）** | 中 | pipeline 图谱粒子背板；components/config 真实系统状态 |

**F7 后已知缺口（非阻塞，联调项）**：`HealthOverview` 的 StatCard `delta` 仍待对比数据；`COMPARE_TAB_READY` 待对比 API；`kibanaLinks` 待消费方接入；报告/诊断/分析页仍需下一轮信息架构与视觉密度优化。

## 11. 开发约束

- 页面不得直接使用 `axios`/`fetch`，应通过 `src/api/*.js`。
- 前端不得直接访问 ES、Kafka、Docker API。
- **图表只进不出**：ECharts 实例只允许存在于 `components/common/charts/`；页面组件传 data/option，禁止页面级 `import echarts`。
- **可视化依赖白名单**：ECharts、`@vue-flow/core`、`@tsparticles/vue3`、`@tsparticles/slim`；不引入 Pinia、大型 UI 组件库等。
- **占位须标注**：F1/F2 占位区块使用 `EmptyState` 并标明 `pending-api` 或阶段说明；mock 数据须可识别为「演示数据」，禁止冒充真实后端数据。
- 系统状态相关页面不能硬编码容器假数据，只能展示后端返回值（F3 已落实，见 §7.2）。
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
| 2026-06-23 | **F2 监控线落地** | `api/logs.js`、`composables/useLogQuery.js`、`components/common/LogTable.vue`、`components/monitor/DynamicFilterBar.vue`、`LogMonitorShell.vue`、`utils/logTypeMeta.js`、`views/monitor/*.vue`（7）、`frontend/DEV.md` §6.6/§10/§12 | 7 监控子页真实 `searchLogs` 查询；字段目录/兜底筛选、分页排序、时间窗联动、错误重试；`npm run build` 通过 | 图表带 `ChartBand` 待 F4（`aggregateLogs`）；`searchByTraceId` 待 F5 链路页；驾驶舱/分析/系统仍占位 |
| 2026-06-23 | **F3 系统线落地（F3-01~09）** | `api/system.js`、`utils/systemStatus.js`、`components/common/StatusCard.vue`、`components/system/PipelineGraph.vue`、`VerifyOutputPanel.vue`、`ConfigSnapshotCard.vue`、`views/system/pipeline.vue`、`components.vue`、`config.vue`、`frontend/DEV.md` §6.5/§7/§8/§10/§12 | 三页真实对接 status/verify/health；六组件矩阵 + 四节点链路图 + 配置快照；60s 轮询与错误重试；`npm run build` 通过 | 旧 `index.vue`/`ServiceStatusCard` 保留只读；verify `workers` 等参数未暴露 UI；`getSystemContainers` 预留未用 |
| 2026-06-23 | **F3-10 DEV 文档收敛** | `frontend/DEV.md` | 系统线状态表、三页 API 消费说明、旧页迁移关系、兜底规则与 `systemStatus.js` 对齐确认 | F4+ 开发前以本文档 §6.5/§7 为系统线基线；**与总体规划差异**：① `/temp/developer` 复用 `components.vue` 而非旧 `index.vue` 独立布局（能力等价、入口更简）；② 旧 `index.vue`/`ServiceStatusCard` 保留文件未删，仅供对照；③ verify 的 `count`/`kafka_wait`/`es_wait` 未暴露页面参数（与旧页一致，仅 `workers` 由验证面板传入） |
| 2026-06-23 | **F4-01 metrics API** | `api/metrics.js` | 六模板 `query*` → `aggregateLogs`；`USE_MOCK=false`；mock 形态 `{ group_by, buckets, took_ms }` | 离线调试可临时 `USE_MOCK=true` |
| 2026-06-23 | **F4-02 useMetrics** | `composables/useMetrics.js` | 六模板枚举、`useTimeRange` debounce 300ms、loading/error/data、`isMock` | — |
| 2026-06-23 | **F4-03 ChartBand** | `components/monitor/ChartBand.vue` | `chartTemplates` 驱动 2~3 图；Trend/Bar/Pie；单图错误重试与演示角标 | Shell 已传 `logType` |
| 2026-06-23 | **F4-04 chartTemplates** | `utils/logTypeMeta.js` | 七类各 2~3 模板对象，对齐总体规划 §3.2 | — |
| 2026-06-23 | **F4-05 HealthOverview** | `components/dashboard/HealthOverview.vue` | Gauge 健康分 + 五 StatCard；三模板并行；环比箭头未做 | 活跃预警数占位；F6-07 / F7-02 |
| 2026-06-23 | **F4-06 流量/耗时面板** | `TrafficErrorPanel.vue`、`LatencyPanel.vue` | 流量错误叠加、错误分布横条+环、耗时三系列折线 | — |
| 2026-06-23 | **F4-07 驾驶舱装配** | `views/dashboard/index.vue`、`AlertDigest.vue`、`LatestReportCard.vue` | 五区块编排；预警/报告 mock 路径 + 演示角标；可跳转 | alerts/reports `USE_MOCK` 待 F6 |
| 2026-06-23 | **F4-08 漏斗页** | `views/analysis/funnel.vue`、`FunnelMain.vue`、`LossLocator.vue` | 五步漏斗+转化率、流失错误码横条、跳转监控 query | 时段对比、监控 query 解析待 F7 |
| 2026-06-23 | **F4-09 DEV 文档收敛** | `frontend/DEV.md` | §6.7~6.11 metrics/驾驶舱/ChartBand/漏斗数据源与 `USE_MOCK` 策略；§3.1/3.2/3.7 差异表；§8 F4 验收；§10 状态表更新 | F5/F6 开发前必读 §6.7 与 §6.11；Shell 补 `logType` 为小改项 |
| 2026-06-23 | **F5-01 诊断/分析 API** | `api/diagnosis.js`、`api/analysis.js` | `submitDiagnosis` 规则 mock；`triggerAnalysisRun` 120s + `node_trace` 降级读取；文档注明 diagnosis 无 `node_trace` | F6 切 `USE_MOCK=false` |
| 2026-06-23 | **F5-02 诊断输入区** | `DiagnosisEntryPanel.vue` | 活跃预警/路由上下文/时间窗驱动 payload；无手工粘贴日志入口 | F5-06 装配 |
| 2026-06-23 | **F5-03 结论区** | `ConclusionPanel.vue` | 双仪表先于文字、根因卡、规则降级角标、空态 EmptyState | — |
| 2026-06-23 | **F5-04 证据区** | `EvidenceTimeline.vue`、`ServiceTopology.vue` | props 驱动时间轴/拓扑/迷你柱图 | — |
| 2026-06-23 | **F5-05 建议区+推断图** | `SuggestionChecklist.vue`、`LangGraphFlow.vue`、`DiagnosisStageRing.vue` | 可勾选清单；诊断页 `node_trace` 五阶段 Vue Flow 推断图；报告页保留阶段环兼容 | 未改 `common/StageRing` |
| 2026-06-23 | **F5-06 诊断页装配** | `views/analysis/diagnosis.vue` | 四区 grid、`submitDiagnosis` + `fetchNodeTrace`、全局 loading/error、mock 角标 | F6 深度诊断可消费 |
| 2026-06-23 | **F5-07 链路检索/瀑布** | `TraceSearchBar.vue`、`TraceWaterfall.vue` | 检索 emit + localStorage 历史；CSS 泳道 + ERROR 着色 + 断点 | F5-08 装配 |
| 2026-06-23 | **F5-08 链路页装配** | `views/analysis/trace.vue` | `searchByTraceId`、`route.query.trace_id` 自动检索、空/错态 + 重试 | — |
| 2026-06-23 | **F5-09 DEV 文档收敛** | `frontend/DEV.md` | §6.12~6.15 诊断/链路数据源、`node_trace` 映射、§5 耦合落地表；§8 F5 验收；§10 状态表 | F6 开发前必读 §6.12 与 §6.15 |
| 2026-06-23 | **F6-01 reports API** | `api/reports.js` | `getRecentReports`/`getReportDetail` 对齐信封 `data`；mock `items+total+limit` / `report:null`；**`USE_MOCK=false`** | 离线可临时 true |
| 2026-06-23 | **F6-02 alerts API** | `api/alerts.js` | `getActiveAlerts`/`acknowledgeAlert` 契约注释；mock `items+total`；**`USE_MOCK=false`** | TopBar 读 `total` |
| 2026-06-23 | **F6-03 reports 三组件** | `ReportTimeline.vue`、`ReportRiskPanel.vue`、`ReportSections.vue` | props 驱动；时间轴选中；风险 Gauge；三节要点 + 页脚 `DiagnosisStageRing` + 统计模式角标 | RelationInsightCard 占位 |
| 2026-06-23 | **F6-04 reports 页装配** | `views/analysis/reports.vue` | mount 拉列表默认选最新；详情联动；空态/错误重试；mock 角标 | — |
| 2026-06-23 | **F6-05 alerts 三组件** | `AlertBoard.vue`、`AlertTable.vue`、`AlertDetailDrawer.vue` | 三态计数+24h 趋势；表格 ack emit；抽屉三段解释+诊断 emit | F6-06 装配 |
| 2026-06-23 | **F6-06 alerts 页装配** | `views/analysis/alerts.vue` | `getActiveAlerts` 驱动看板+表；ack 刷新；抽屉；诊断 query；30s 静默轮询 | — |
| 2026-06-23 | **F6-07 全局接线** | `TopBar.vue`、`AlertDigest.vue`、`LatestReportCard.vue` | 角标/摘要真实 API；移除演示兜底与角标；30s 轮询 | ack 后下次轮询更新角标；HealthOverview 权重仍占位 |
| 2026-06-23 | **F6-08 DEV 文档收敛** | `frontend/DEV.md` | §6.7.2/§6.8/§6.11 更新；§6.16~6.18 报告/预警/全局接线；§8 F6 验收；§10 状态表；§12 F6 日志 | F7 增强前以本文档 §6.16~6.18 为结果线基线 |
| 2026-06-23 | **F7-01 关系洞察卡** | `RelationInsightCard.vue`、`reports.vue` | 箭头卡 + 双 TrendChart 迷你折线；空数据 v-if；mock 演示角标；已传 `relations/relation_chain` | 后端需提供稳定 relation_chain |
| 2026-06-23 | **F7-02 双窗口对比** | `StatCard.vue`、`funnel.vue` | 环比 props（未传隐藏）；漏斗对比 tab 编排 + `COMPARE_TAB_READY=false` | HealthOverview 待传 delta；对比 API 就绪后改 true |
| 2026-06-23 | **F7-03 Kibana 深链** | `.env.example`、`kibanaLinks.js` | Discover/Dashboard URL 生成；无 env 返回 null | 消费方待 import |
| 2026-06-23 | **F7-04 动效抛光** | `index.css`、`BaseChart.vue` | 400ms 图表过渡、page-section hover、reduce-motion | — |
| 2026-06-23 | **F7-05 粒子背板** | `ParticleBackdrop.vue`、`@tsparticles/vue3`、dashboard/pipeline/diagnosis 三页 | P-01~P-07 通过；白名单各 1 处；静态降级 | **已启用，未跳过** |
| 2026-06-23 | **体验收口-可视化深化** | `common/charts/*`、`utils/chartTheme.js`、`ParticleBackdrop.vue`、`LangGraphFlow.vue`、`DiagnosisEntryPanel.vue`、`SuggestionChecklist.vue`、`views/analysis/diagnosis.vue`、`vite.config.js`、`package.json` | 引入 Vue Flow 与 tsParticles；统一全站图表主题；诊断页去除手工粘贴日志逻辑，改为上下文取证 + LangGraph 推断图；构建分包降低主 chunk | 下一轮可继续做报告/预警/系统页的信息密度与微交互抛光 |
| 2026-06-23 | **F7-06 DEV 文档收敛** | `frontend/DEV.md` | §6.19 F7 增强；§8 F7 验收；§10.1 F1~F7 里程碑总览 + §10.2 模块状态；§12 F7 日志 | 联调项见 §10.2 底部缺口清单 |
| 2026-06-23 | **全量前后端联调修复 metrics** | `api/metrics.js` | 六模板改传 `template` 走 `POST /logs/aggregate` 预置路由，修复驾驶舱 error_code 白名单报错与 `extra.by_service` 缺失 | 需配合后端 `aggregate_by_template`；时间窗内无日志时指标仍为 0（数据时效问题） |
| 2026-06-23 | **体验收口第一轮** | `assets/styles/index.css`、`layout/index.vue`、`layout/components/TopBar.vue`、`SidebarTreeNode.vue`、`components/common/*`、`components/common/charts/GaugeChart.vue`、`components/monitor/ChartBand.vue`、`ChartBandItem.vue`、`frontend/DEV.md` | 修复 `ChartBandItem` runtime template 导致监控图表空白；Gauge 标题/数值不再重叠；统一背景、卡片、侧栏、顶部栏、指标卡、空态与图表 overlay 的基础质感；`npm.cmd run build` 通过，浏览器抽查无控制台 warn/error | 下一轮重点：Dashboard 首屏重新编排、诊断页默认态信息密度、报告/预警页长文本与表格体验、系统页慢接口加载态 |
| 2026-06-23 | **规则子图返回解析修复** | `views/analysis/diagnosis.vue`、`frontend/DEV.md` | `/analysis/run` 成功但 `/reports/{id}` 暂未读到详情时，诊断页改用同次返回的 `alert_decision.alert_candidate/explanation` 渲染结论、严重度、置信度、证据、建议与受影响服务；`npm.cmd run build` 通过 | 后端报告详情仍依赖 ES 写后读；前端保留详情优先、即时结果兜底策略 |
| 2026-06-23 | **智能分析 5 页战术 UI 全量落地** | `package.json`、`package-lock.json`、`vite.config.js`、`components/common/AnalysisWorkbench.vue`、`TacticalKpiStrip.vue`、`G6RelationGraph.vue`、`DigitalTwinScene.vue`、`ReasoningInspector.vue`、`views/analysis/diagnosis.vue`、`reports.vue`、`alerts.vue`、`trace.vue`、`funnel.vue`、`frontend/DEV.md` | 按高密度战术工作台重排 5 个智能分析页面；新增 G6 关系图、Three.js 数字孪生态势、LangGraph 中间推理检查器、KPI 条与深色硬朗视觉基座；漏斗时间窗对比 tab 已启用；`npm.cmd run build` 通过；浏览器验证 5 个页面均可渲染，漏斗 tab 交互无新增 warn/error | G6/Three 带来较大独立 chunk，已在 `vite.config.js` 拆分；后续如追求首屏极限性能，可把分析路由进一步懒加载 |
| 2026-06-24 | **智能分析 5 页低饱和硬朗风格与页面目的重排** | `components/common/AnalysisWorkbench.vue`、`TacticalKpiStrip.vue`、`ReasoningInspector.vue`、`G6RelationGraph.vue`、`DigitalTwinScene.vue`、`RiskLevelStrip.vue`、`HorizontalReportTimeline.vue`、`InsightArtifactPanel.vue`、`utils/chartTheme.js`、`views/analysis/diagnosis.vue`、`reports.vue`、`alerts.vue`、`trace.vue`、`funnel.vue`、`frontend/DEV.md` | 统一黑白灰高对比、斜切标识、蓝青状态光、红橙告警强调与低饱和配色；推理路径改为顶部 compact 次级组件；诊断页前置规则聚类/top_k/子图图谱；报告页改横向可缩放时间轴；预警页补购物高峰与成功预警持久化；调用链路页移除手动检索并消费预警链；漏斗页聚焦埋点分析产物与三维漏斗投影；Three.js 由服务环改为时间/风险/类型/次数多维投影；`npm.cmd run build` 通过；浏览器验证 5 个智能分析路由均可渲染且新错误为 0 | G6/Three 仍为大 chunk，当前通过 manualChunks 隔离；如后续追求首屏极限性能，可对分析页可视化组件进一步做路由级懒加载 |
| 2026-06-24 | **智能分析页头部去重与 TopBar 承载** | `composables/usePageHeader.js`、`layout/components/TopBar.vue`、`components/common/AnalysisWorkbench.vue`、`frontend/DEV.md` | 新增页面头部状态 composable；`AnalysisWorkbench` 不再渲染 main 内部标题区，改为向全局 `TopBar` 注册 title/eyebrow/subtitle/tone，并将 actions 挂载后 Teleport 到顶部栏；分析页 `TopBar` 切换为低饱和硬朗深色样式，普通页面保持原头部；`npm.cmd run build` 通过；浏览器验证分析页仅 1 个 h1、`.analysis-workbench__header=0`、顶部 actions 可见、路由切换无新 error | actions 依赖顶部栏 `#topbar-page-actions` 容器；若未来改 Layout 顺序，需要保留该挂载点 |
| 2026-06-24 | **智能分析 main 白边移除** | `layout/index.vue`、`components/common/AnalysisWorkbench.vue`、`frontend/DEV.md` | 为 `/analysis/*` 路由增加 `main--analysis` 布局模式，去掉 main 外层 `24px` padding 并改为深色背景；`AnalysisWorkbench` 去掉外边框和圆角，最小高度适配顶部分析头部，使智能分析工作台贴边铺满主内容区；`npm.cmd run build` 通过；浏览器验证 `mainPadding=0px`、工作台与 main `deltaLeft/deltaTop=0`、工作台 `border/radius=0`、无新 error | 该贴边策略仅作用于智能分析路由，Dashboard/监控/系统页仍保留原 main padding |
| 2026-06-24 | **报告可视化填充与预警交互修正** | `views/analysis/reports.vue`、`views/analysis/alerts.vue`、`components/analysis-alerts/AlertTable.vue`、`frontend/DEV.md` | 周期体检报告中含 G6/Three 的面板改为 grid 填充，图谱和三维投影容器最小高度提升并撑满单元；预警中心严重度分区/服务图谱交互改为只刷新右侧“预警处置上下文”，不再打开抽屉；预警明细表格增加 430px 独立滚动区和 sticky 表头，避免整页被明细拉长；`npm.cmd run build` 通过；浏览器验证图谱/投影高度提升、表格 `overflowY=auto` 且内部可滚动 | 表格行点击仍保留打开详情抽屉，用于查看完整明细；严重度分区只做上下文选择 |
| 2026-06-24 | **表格 UI 统一为低饱和硬朗风格** | `components/analysis-alerts/AlertTable.vue`、`components/common/LogTable.vue`、`frontend/DEV.md` | 统一 AlertTable 与 LogTable 的深色表格皮肤：低饱和黑灰背景、细边线、sticky 表头、深色滚动条、2px 斜切/硬朗按钮、低饱和状态色与 skeleton；保留预警表格独立滚动与日志表分页/展开/排序能力；`npm.cmd run build` 通过；浏览器验证预警表格背景/表头/文字色/滚动/sticky 均生效且无新 error | 当前项目仅这两套 `<table>` 组件；后续新增表格应复用这套视觉规则，避免再引入浅色表格 |
