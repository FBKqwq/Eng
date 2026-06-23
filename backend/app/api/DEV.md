# API 模块 DEV 文档

## 1. 文档用途说明
本文档用于辅助 Agent 快速理解 API 模块状态、开发边界、已实现能力、待开发事项和开发日志，避免重复实现与越层开发。所有 Agent 在修改 `app/api/` 前必须先读本文档，完成开发后必须同步更新“模块状态表”和“开发日志区”。

## 2. 项目模块总览
| 子模块 | 路径 | 当前定位 |
|---|---|---|
| 路由聚合 | `app/api/router.py` | 统一挂载 v1 路由 |
| 健康检查 | `app/api/v1/health.py` | 服务可用性探活 |
| 日志查询接口 | `app/api/v1/logs.py` | 日志查询入口 |
| 智能诊断接口 | `app/api/v1/diagnosis.py` | 诊断入口 |
| 系统状态接口 | `app/api/v1/system.py` | 运行状态查询与全链路验证入口 |
| 分析报告接口 | `app/api/v1/reports.py` | 最近报告与报告详情（M4 真实调 `report_service`） |
| 预警接口 | `app/api/v1/alerts.py` | 活跃预警与确认（M5 真实调 `alert_service`） |
| 分析轨迹接口 | `app/api/v1/analysis.py` | 近期图执行轨迹与手动触发主图（M6 真实调 `graph_main` / `report_service`） |

## 3. 模块职责边界
- 应该放在这里：请求接收、基础校验、调用 service、统一响应返回。
- 不应该放在这里：Kafka/ES 直连代码、复杂业务规则、诊断核心算法。

## 4. 已实现功能清单
- 已提供 health/logs/diagnosis/system/reports/alerts 六类 v1 接口文件。
- 已具备路由聚合入口文件。
- `POST /api/v1/system/pipeline/verify` 已接入后端全链路验证服务，返回节点状态与终端输出。
- `GET /api/v1/logs/fields`：按 `log_type` 返回字段目录或全量列表（M1，调 `field_catalog`）。
- `POST /api/v1/logs/aggregate`：受控聚合入口（M1，调 `aggregation_service`）。
- `GET /api/v1/reports/recent`、`GET /api/v1/reports/{id}`：真实调 `report_service`（M4-05）。
- `GET /api/v1/alerts/active`、`POST /api/v1/alerts/{id}/ack`：真实调 `alert_service`（M5-05）。
- `GET /api/v1/analysis/runs/recent`、`POST /api/v1/analysis/run`：真实调 `report_service` / `graph_main`（M6-05）；见下文「分析轨迹 API」。

## 4.1 分析轨迹 API 与 node_trace 展示用途（M6）

路由前缀：`/api/v1/analysis`（`router.py` 已注册 `tags=["analysis"]`）。

### `GET /api/v1/analysis/runs/recent`

- **职责**：返回近期分析报告列表，并附带每条报告的 **node_trace 摘要**，供前端「分析执行轨迹」面板展示。
- **实现**：先 `list_recent_reports(limit)`，再对每条 `report_id` 调 `get_report` 补全 `node_trace`（列表项本身不含完整轨迹）。
- **响应字段**（`ApiResponse[AnalysisRunsData]`，统一信封，业务字段在 `data` 内）：
  - `data.items[]`：`report_id`、`report_type`、`title`、`created_at`、`trigger_type`
  - `data.items[].node_trace[]`：摘要字段 `node_name`、`status`、`duration_ms`、`output_summary`
  - `data.items[].node_count`、`data.items[].total_duration_ms`：便于前端渲染节点数与总耗时

### `POST /api/v1/analysis/run`

- **职责**：手动触发主图 `run_main_graph`，用于调试、答辩演示或前端「立即分析」按钮。
- **请求体**（`AnalysisRunRequest`）：`trigger_type`（`scheduled` | `rule`）、可选 `trigger_event`、`time_window`。
- **响应字段**（`ApiResponse[AnalysisRunData]`，统一信封）：`ok` 在信封层；`data` 内含 `report_id`、`alert_id`、**完整 `node_trace`**、`alert_decision`、`errors`。

### node_trace 前端展示用途

| 场景 | 数据来源 | 前端可展示内容 |
|---|---|---|
| 历史轨迹列表 | `GET /runs/recent` | 按报告折叠展示节点流水线：节点名、成功/失败状态、单节点耗时、产出摘要 |
| 手动触发即时反馈 | `POST /run` | 完整轨迹时间线；结合 `alert_decision` 展示是否出预警、是否去重命中 |
| 报告详情深挖 | `GET /reports/{id}` | 报告正文 + 持久化时写入的完整 `node_trace`（含子图节点，主图前缀 `scheduled.` / `rule.`） |

- 子图节点在 `merge_result` 阶段合并入主图轨迹，前端可用 `node_name` 前缀区分主图节点与子图节点。
- `output_summary` 为短文本，适合列表卡片；详情页可展开 `error_message`（若存在）。

## 4.2 前端对接接口契约（2026-06-23 统一信封改造后）

> 统一前缀 `/api`；本机后端默认 `http://localhost:8000`。CORS 已放行 `localhost:5173` / `127.0.0.1:5173`。
>
> **统一响应信封（所有 v1 业务接口，2026-06-23 已落地）**：
> ```jsonc
> { "ok": true,  "data": { ...业务负载... }, "error": null }
> { "ok": false, "data": null 或 降级数据,    "error": { "code": "...", "message": "..." } }
> ```
> - 前端固定判定：先看 `ok`；`ok===true` 取 `data`，`ok===false` 取 `error.code` / `error.message`。
> - 不再有 `available` / `placeholder` / 顶层 `message` 等旧约定，原 service 字段统一下沉到 `data`。
> - 部分失败仍可能带降级 `data`（如 ES 离线时 `logs/aggregate` 返回空 `buckets`），前端应优先以 `ok` 为准。
> - 信封定义见 `app/schemas/response.py`（`ApiResponse[T]` / `ErrorInfo` / `ApiCode`）；每个接口都标注了 `response_model=ApiResponse[XxxData]`，可在 `/docs`(OpenAPI) 查看强类型 `data` 结构。
> - **例外**：请求体/参数校验失败由 FastAPI 直接返回 `422 { detail:[...] }`（不走业务信封），前端需对 422 单独处理。
>
> **错误码（`ApiCode`）**：`es_unavailable`、`query_failed`、`invalid_param`、`not_found`、`diagnosis_failed`、`graph_failed`、`internal_error`。

| 方法 | 路径 | 请求体/参数 | `data` 关键字段（实测；统一包在 `{ok,data,error}` 内） |
|---|---|---|---|
| GET | `/api/v1/health` | — | `{ status:"ok" }` |
| GET | `/api/v1/system/status` | — | `{ kafka_bootstrap_servers, kafka_topic, elasticsearch_hosts, elasticsearch_index_pattern, kafka{available,brokers_count,topics_count,configured_topic}, elasticsearch{available,cluster_status,docs_count,indices_count,...}, docker{available,...}, containers{<svc>:{status}}, services{...} }` |
| GET | `/api/v1/system/containers` | — | `{ project, available, error, containers{kafka,elasticsearch,logstash,kibana,setup} }` |
| POST | `/api/v1/system/pipeline/verify` | `{ count, workers(1~8), kafka_wait, es_wait }` | `PipelineVerifyResponse`（节点状态 + 终端输出，耗时长，依赖在线链路） |
| POST | `/api/v1/logs/search` | `LogQueryRequest`（见下） | `{ items[], total, page, page_size, has_more, took_ms }`；`items[]`：`{ log_id, timestamp, log_level, log_type, event_type, service_name, message, trace_id, request_id, user_id, status, summary, payload{原始完整文档} }`。ES 离线：`ok:false`+`error.code:es_unavailable`，`data` 为空页 |
| GET | `/api/v1/logs/fields` | `?log_type=`（可选） | 不带参：`{ registered_log_types[] }`（`log_type`/`catalog` 为 null）；带参：`{ log_type, catalog{ filter_fields[], terms_fields[], metric_fields[], ... } }`；非法类型：`ok:false`+`error.code:invalid_param` |
| POST | `/api/v1/logs/aggregate` | `LogAggregateRequest`（见下） | `{ group_by, interval, buckets[{key,count,value?,extra?}], took_ms, extra? }`。ES 离线：`ok:false`+`error.code:es_unavailable`，`data.buckets` 为空 |
| POST | `/api/v1/diagnosis` | `DiagnosisRequest`（`request_id` 必填，常用 `keyword`/`service_name`/`error_code`/`time_range_start`/`time_range_end`） | `{ message, input{回显}, diagnosis{ anomaly_type, severity, route, root_cause, suggestion[], evidence_logs[], context_summary{} } }`（同步规则诊断门面，`ok` 恒 true；LLM 深挖走 analysis） |
| GET | `/api/v1/reports/recent` | `?limit=`(1~100,默认20) | `{ items[{report_id, report_type(periodic|event), title, risk_level, summary, created_at, task_id}], total, limit }`；查询失败：`ok:false`+`error.code:query_failed` |
| GET | `/api/v1/reports/{report_id}` | path `report_id` | `{ report_id, report{完整报告含 node_trace} }`；**未命中**：`ok:true`、`data.report=null`（仍 200，非 404） |
| GET | `/api/v1/alerts/active` | `?limit=`(1~200,默认50) | `{ items[{alert_id, alert_type, severity, status, title, affected_service, evidence_count, created_at, updated_at}], total }` |
| POST | `/api/v1/alerts/{alert_id}/ack` | body `{ operator? }` | `{ alert_id, status:"acknowledged" }`；确认失败：`ok:false`+`error.code:query_failed`，`data` 回显 `alert_id` |
| GET | `/api/v1/analysis/runs/recent` | `?limit=`(1~100,默认20) | `{ items[{report_id, report_type, title, created_at, trigger_type, node_trace[{node_name,status,duration_ms,output_summary}], node_count, total_duration_ms}], total, limit }` |
| POST | `/api/v1/analysis/run` | `{ trigger_type:"scheduled"|"rule", trigger_event?{}, time_window?{} }` | `{ report_id, alert_id, node_trace[完整], alert_decision{should_alert,is_duplicate,existing_alert_id,idempotency_key,explanation}, errors[] }`（同步执行，scheduled 跑完整定时子图，耗时数十秒；图执行失败：`ok:false`+`error.code:graph_failed` 且 `data` 仍带轨迹） |

**`LogQueryRequest` 常用字段**（全部可选，分页有默认值）：`start_time`、`end_time`（ISO-8601，建议带时区，如 `2026-06-22T16:00:00Z`）、`service_names[]`、`log_levels[]`(DEBUG/INFO/WARNING/ERROR/CRITICAL)、`log_types[]`(behavior/application/web_server/performance/security/infrastructure/audit)、`event_types[]`、`error_codes[]`、`trace_id`、`user_id`、`keyword`、`status_codes[]`、`page`(默认1)、`page_size`(1~500,默认20)、`sort_by`(默认 timestamp)、`sort_order`(asc/desc,默认 desc)。

**`LogAggregateRequest` 字段**：`start_time`、`end_time`（必填，跨度 ≤ 24h）、`group_by`（必填，枚举：log_level/service_name/log_type/event_type/error_code/status_code/user_id/client_ip）、`log_types[]`(可选)、`service_names[]`(可选)、`interval`(1m/1h/1d,可选)、`top_n`(默认10,硬上限50)、`filters`(可选)。

> 时间字段务必使用 UTC（带 `Z` 或 `+00:00`）。不带时区的 naive 时间会被 ES 当作 UTC，在 UTC+8 环境下导致查询窗口偏移、查不到数据（后端 analysis 层已于 2026-06-23 修复同类问题）。

## 5. 待开发功能清单（P0-P3）
- ~~P0：补齐接口错误码与异常返回结构一致性。~~（2026-06-23 已完成：全接口统一 `ApiResponse[T]` 信封 + `ApiCode` 错误码 + `response_model`）
- P1：增加 metrics 类接口并接入服务层。
- P2：补充接口层参数校验与示例响应文档。
- P3：补充 API 访问审计日志与限流策略。

## 6. 模块状态表
| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| API | M1/M4/M5/M6 核心接口已真实对接，全接口统一信封 + response_model | 2026-06-23 | elk-backend-agent | 低 | 响应信封已统一为 `ApiResponse[T]`（`{ok,data,error}`）；全接口 TestClient 实测 + pytest 146 passed |

## 7. 禁止重复实现清单
| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| 日志查询逻辑 | `app/services/elasticsearch/` | 禁止在 `app/api/v1/logs.py` 直接拼 ES 查询 |
| 诊断规则引擎 | `app/services/diagnosis/rule_engine.py` | 禁止在 `app/api/v1/diagnosis.py` 重复写规则分流 |
| Kafka 生产逻辑 | `app/services/kafka/` | 禁止在 API 路由直接写 Kafka Producer |

## 8. 真实实现与设计愿景差异
| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 接口标准化 | 完整统一的请求响应与错误规范 | 已统一 `ApiResponse[T]` 响应信封 + `ApiCode` 错误码 + 全接口 `response_model` | 后续仅需对新增接口沿用同一信封 |

## 9. 开发日志区
| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-05-06 | 初始化 API 模块 DEV 文档 | `app/api/DEV.md` | 建立模块开发维护基线 | 待后续按实际开发持续更新 |
| 2026-05-14 | 日志查询路由与 schema 对齐：`LogSearchRequest` 更名为 `LogQueryRequest` | `app/api/v1/logs.py` | 修复启动期 ImportError，与 `app/schemas/log.py` 一致 | 无 |
| 2026-05-14 | 恢复被基础版本覆盖的系统状态接口 | `app/api/v1/system.py` | `/status` 重新返回 `kafka`、`elasticsearch`、`docker`、`containers`、`services`，并恢复 `/containers` | 需重启当前 8000 后端进程后浏览器才能命中新代码 |
| 2026-05-18 | 新增全链路验证 API | `app/api/v1/system.py` | `POST /system/pipeline/verify` 调用 service 执行 `verify_log_pipeline_full` 并返回结构化节点状态 | 验证耗时取决于 Kafka/Logstash/ES 当前状态 |
| 2026-05-19 | 全链路验证 API 支持多线程参数 | `app/api/v1/system.py` | `PipelineVerifyRequest.workers` 透传到验证 service，覆盖多线程生产验证 | workers 当前由 schema 限制在 1~8 |
| 2026-06-16 | 新增 reports/alerts 占位路由与 logs/fields | `reports.py`、`alerts.py`、`logs.py`、`router.py` | 路由可 import；初期返回 `placeholder: true` | 已由 M4/M5 对接真实 service |
| 2026-06-16 | M1-06：`GET /fields` 与 `POST /aggregate` 真实实现 | `app/api/v1/logs.py` | 转发 field_catalog / aggregation_service；无 placeholder | — |
| 2026-06-22 | M4-05：reports API 去占位 | `app/api/v1/reports.py` | `/recent` 与 `/{id}` 真实调 report_service | — |
| 2026-06-22 | M5-05：alerts API 去占位 | `app/api/v1/alerts.py` | `/active` 与 `/{id}/ack` 真实调 alert_service | — |
| 2026-06-22 | 同步 API DEV 文档至 M5 现状 | `app/api/DEV.md` | 模块总览、已实现清单、状态表与 M1/M4/M5 开发日志对齐 | P0 统一错误码仍待办 |
| 2026-06-22 | M6-05：analysis 轨迹 API | `app/api/v1/analysis.py`、`router.py` | `/runs/recent` 摘要轨迹；`/run` 手动触发主图 | list 项经 get_report 补全 node_trace |
| 2026-06-22 | **M6-07：API DEV 文档收敛** | `app/api/DEV.md` | 分析轨迹 API 与 node_trace 前端展示用途已记录 | P0 统一错误码仍待办 |
| 2026-06-23 | **前端对接前接口契约核对（文档校准，未改代码）** | `app/api/DEV.md` | 用 TestClient 实测全部 v1 接口，新增「4.2 前端对接接口契约」实测表；补记 `POST /logs/search`（此前清单遗漏）；明确 logs/diagnosis 走 `available` 信封、reports/alerts/analysis 走 `ok`+`placeholder` 信封的差异 | 已由当日「统一信封」改造解决 |
| 2026-06-23 | **P0 落地：全接口统一响应信封 + response_model** | 新增 `app/schemas/response.py`；改造 `app/api/v1/{health,logs,diagnosis,system,reports,alerts,analysis}.py`；新增 data 模型于 `schemas/{log,report,alert,diagnosis}.py`、`api/v1/analysis.py`；删除旧 `*Response`(含 placeholder)；同步 `tests/test_health.py`、`tests/test_m6_main.py` | 所有 v1 业务接口统一返回 `ApiResponse[T] = {ok,data,error}`，错误码集中于 `ApiCode`，旧 `available`/`placeholder`/顶层 `message` 全部移除并下沉到 `data`；service 层零改动（API 层适配）。TestClient 实跑 13 接口信封一致；pytest 146 passed/1 skipped | 请求体校验失败仍由 FastAPI 返回 422 `{detail}`（不走业务信封），前端需单独处理；`LogFieldsData` 三字段均序列化（未用到的为 null），前端按非空判断 |

## 2026-05-13 补充：开发者容器状态 API

### 变更记录

| 日期 | 变更 | 涉及文件 | 说明 | 状态 |
| --- | --- | --- | --- | --- |
| 2026-05-13 | 新增开发者容器状态 API | `app/api/v1/system.py` | `GET /api/v1/system/status` 增加 `docker`、`containers`、`services` 字段；新增 `GET /api/v1/system/containers` 独立返回 Docker 容器状态 | 已通过 TestClient 验证 |

### `GET /api/v1/system/status`

保留原有 Kafka / Elasticsearch 配置字段：

- `kafka_bootstrap_servers`
- `kafka_topic`
- `elasticsearch_hosts`
- `elasticsearch_index_pattern`

新增开发者监控字段：

- `docker.available`：后端是否成功访问 Docker CLI / Docker API。
- `docker.error`：Docker 查询失败原因，成功时为 `null`。
- `containers`：按服务名聚合的容器状态，当前包含 `kafka`、`elasticsearch`、`logstash`、`kibana`、`setup`。
- `services`：与 `containers` 同结构，保留给前端语义化读取。

### `GET /api/v1/system/containers`

只返回 Docker 查询结果，适合开发者页面、调试工具或后续运维面板单独调用。

### 状态值约定

- `running`：Docker 原始 `State` 为 `running`。
- `down`：容器存在但不是运行态，例如 `exited`。
- `unknown`：容器未找到，或 Docker 查询不可用。

## 2026-05-13 补充：系统配置快照增强

### 模块状态表更新

| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
| --- | --- | --- | --- | --- | --- |
| API | 可用但需完善 | 2026-05-13 | codex | 中 | `/api/v1/system/status` 已透出 Kafka 与 Elasticsearch 结构化运行快照，接口层只负责调用 service 并组装响应 |

### 开发日志区

| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
| --- | --- | --- | --- | --- |
| 2026-05-13 | 增强系统配置快照接口 | `app/api/v1/system.py` | 新增 `kafka`、`elasticsearch` 快照字段，保留原基础配置字段和 Docker 容器字段 | 真实状态依赖本机 Kafka、Elasticsearch、Docker 可访问 |
