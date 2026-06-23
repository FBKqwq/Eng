# Elasticsearch 服务模块 DEV 文档

## 1. 文档用途说明

本文档用于维护 `app/services/elasticsearch/` 的实现状态和边界，确保日志查询、索引访问与 ES 客户端能力集中治理，避免接口层和其他服务越层操作 ES。所有 Agent 在继续开发前应先阅读，并在完成开发后同步更新「模块状态表」和「开发日志区」。

## 2. 项目模块总览

| 文件 | 主要职责 | M1 状态 |
|---|---|---|
| `client.py` | Elasticsearch 客户端封装（含 `basic_auth`、凭证去引号） | 真实实现 |
| `log_query_service.py` | 日志 bool 查询、分页、`search_recent_context`（诊断兼容入口） | 真实实现 |
| `cluster_status.py` | 集群健康快照（info / cluster.health / index count） | 真实实现 |
| `field_catalog.py` | 7 类日志字段目录、聚合白名单校验、`resolve_index_pattern` | **M1 真实实现** |
| `index_service.py` | component / index 模板创建、`init_all_indices`、`verify_templates` | **M1 真实实现** |
| `aggregation_service.py` | 六类受控聚合模板 + 统一 `aggregate()` 入口 | **M1 真实实现** |
| `context_service.py` | trace / 服务窗口 / 同类错误 / 用户行为四类诊断上下文 | **M1 真实实现** |

## 3. 模块职责边界

- 应该放在这里：ES 客户端连接、查询构建、聚合 DSL、索引模板管理、结果转换。
- 不应该放在这里：HTTP 参数处理、诊断规则分流、Kafka 生产逻辑。
- 索引 pattern 解析统一调用 `field_catalog.resolve_index_pattern()`，禁止在其他模块重复实现。
- `search_recent_context()` 留在 `log_query_service.py`；诊断上下文新能力走 `context_service.py`。

## 4. 已实现功能清单

### 基础能力（M1 前已落地）

- `get_es_client()`：配置非空密码时通过 `basic_auth` 连接 ES，兼容无安全认证的本地开发；对 `.env` 凭证去外层引号。
- `search_logs()`：基于 `LogQueryRequest` 构建 bool 查询，支持分页、排序、关键词、时间范围和常见字段过滤；ES 不可用时返回 `available: false` 稳定错误结构。
- `search_recent_context()`：为诊断服务提供受控的相关日志上下文查询入口（M1-05 不得修改此函数）。
- `get_elasticsearch_health_snapshot()`：读取 ES info、cluster.health 与 index pattern count，外部连接失败时返回 `available=false`。

### M1 新增能力（2026-06-16 验收通过）

**field_catalog.py**

- `FIELD_CATALOG`：7 类 log_type（behavior / application / web_server / performance / security / infrastructure / audit）完整注册。
- `get_catalog_for_log_type()` / `list_registered_log_types()`：字段目录查询；未知类型返回 `ok=false` 与明确 message。
- `validate_aggregate_field()`：filter / terms / metric 三类白名单校验，拒绝 `message` 等文本字段聚合。
- `validate_aggregate_request()`：聚合请求级校验（group_by 合法性、字段白名单）。
- `resolve_index_pattern()`：单类型 / 多类型 / 空列表三种 index pattern 解析。

**index_service.py**

- `create_component_templates()` / `create_index_templates()` / `create_analysis_indices()`：按 log_type 拆分索引模板与分析索引模板。
- `init_all_indices()`：依次创建全部模板，供 `init_indices` task 调用。
- `verify_templates()`：只读校验关键模板是否存在。

**aggregation_service.py**

- `aggregate()`：统一聚合入口，校验 field_catalog 后组装 DSL 并执行。
- 六类模板：`aggregate_traffic` / `aggregate_errors` / `aggregate_latency` / `aggregate_behavior_funnel` / `aggregate_security` / `aggregate_infra_health`。
- 约束：`top_n` 上限 50、时间窗 ≤ 24h、ES 失败返回 `available=false`；返回值不含 `placeholder`。

**context_service.py**

- `get_trace_context()`：跨索引查同 trace 日志，按 timestamp 升序。
- `get_service_window()`：服务时间窗口 + level 分布 + 直方图。
- `get_similar_errors()`：同类错误检索与聚合统计。
- `get_user_recent_actions()`：用户近期行为日志。
- 约束：`limit` ≤ 50、时间窗 ≤ 24h、ES 失败 `available=false`。

**API 层（M1-06，见 `app/api/v1/logs.py`）**

- `GET /api/v1/logs/fields`：按 log_type 返回字段目录（双模式：单类型 / 全量列表）。
- `POST /api/v1/logs/aggregate`：转发 `aggregation_service.aggregate()`。

### 拆索引链路对齐（2026-06-16 基础设施 + 后端）

- **Logstash**（`location/logstash/pipeline/logstash.conf`）：Kafka 业务日志按 `log_type` 写入 `app-logs-{log_type}-YYYY.MM.dd`；缺 `log_type` 时写入 `app-logs-unknown-YYYY.MM.dd`。
- **索引命名约定**：文档字段 `log_type` 使用枚举值（如 `web_server`）；ES 索引名片段与 `log_type` 相同（保留下划线），例如 `app-logs-web_server-*`；component template 名 `logs-web-server` 仅用于 ES 模板组合，不参与索引路由。
- **后端查询**：`aggregation_service._resolve_search_index()` 直接调用 `resolve_index_pattern()`，指定 `log_types` 时查询对应拆分索引，不再强制回退 `app-logs-*`。
- **未指定 log_types**：仍使用 `settings.elasticsearch_index_pattern`（默认 `app-logs-*`），可命中全部拆分索引及历史统一索引。

## 5. 待开发功能清单（P0-P3）

- P1：聚合缓存与慢查询保护（演示稳定性）。
- P2：结合实际 mapping 优化高亮、排序与慢查询告警。
- P2：`log_query_service.search_logs` 支持按 log_type 默认路由到拆分索引（当前仍用全局 pattern）。
- P3：真实 ES 环境下的 integration 压测与异常数据回归。

> M1 P0 项（field_catalog / index_service / aggregation / context 真实实现）已全部完成，不再列入待开发。

## 6. 模块状态表

| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/Agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| client.py | 稳定可用 | 2026-05-14 | elk-backend-agent | 低 | basic_auth 与凭证去引号已验证 |
| log_query_service.py | 稳定可用 | 2026-05-18 | codex | 低 | 真实 ES search；诊断兼容入口保留 |
| cluster_status.py | 稳定可用 | 2026-05-13 | elk-backend-agent | 低 | `/system/status` 可展示 cluster 快照 |
| field_catalog.py | 拆索引已对齐 | 2026-06-16 | elk-backend-agent | 低 | web_server 索引 segment 保留下划线 |
| index_service.py | M1 已完成 | 2026-06-16 | elk-backend-agent (M1-02) | 低 | 模板 pattern `app-logs-{log_type}-*` |
| aggregation_service.py | 真实 ES 端到端验证通过 | 2026-06-23 | elk-backend-agent (e2e) | 低 | 修复 `_terms_field` 误加 `.keyword`；terms 聚合对真实 ES 返回正常 |
| context_service.py | M1 已完成 | 2026-06-16 | elk-backend-agent (M1-05) | 低 | 四上下文函数；未指定 type 仍查 `app-logs-*` |

## 7. 禁止重复实现清单

| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| ES 查询构建 | `app/services/elasticsearch/` | 禁止在 `api/v1/logs.py` 直接拼 DSL |
| ES 客户端连接 | `app/services/elasticsearch/client.py` | 禁止在多个模块重复初始化客户端 |
| 索引 pattern 解析 | `field_catalog.resolve_index_pattern()` | 禁止在 aggregation / context 中硬编码 pattern |
| 聚合白名单校验 | `field_catalog.validate_aggregate_*()` | 禁止在 aggregation_service 重复维护字段列表 |
| 索引模板管理 | `index_service.py` | 禁止在 task 或 API 层直接调用 ES 模板 API |
| 诊断上下文 | `context_service.py` | 禁止扩展 `log_query_service.search_recent_context` 替代本模块 |

## 8. 真实实现与设计愿景差异

| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 按 log_type 拆索引 | Logstash 路由至 `app-logs-{log_type}-*`，各类型独立 mapping | **已生效**：Logstash 按 `log_type` 拆分写入；后端聚合指定 type 时查拆分索引 | 历史统一索引 `app-logs-YYYY.MM.dd` 可择机清理或 reindex |
| 索引命名 | 文档 log_type 与索引 segment 一致 | `web_server` 字段 → `app-logs-web_server-*` 索引（下划线） | 总体规划文档中 `web-server` 连字符表述与实现对齐说明 |
| 日志列表查询 | 监控页按类型查对应索引 | `search_logs` 仍默认 `app-logs-*` 全量 pattern | P2 可按请求 log_type 路由拆分索引 |
| 高可用日志查询 | 结构化、高性能、可扩展查询能力 | search / health / 聚合 / 上下文均已真实 ES 实现 | 结合真实索引 mapping 继续优化慢查询保护 |

## 9. 开发日志区

| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-05-06 | 初始化 Elasticsearch 模块 DEV 文档 | `DEV.md` | 建立查询模块维护基线 | — |
| 2026-05-13 | 新增 ES 集群健康快照 | `cluster_status.py` | `/system/status` 可展示 cluster_status | 依赖 ES 可访问 |
| 2026-05-14 | ES 客户端 basic_auth 与凭证去引号 | `client.py` | 修复 `.env` 引号导致检索为空 | 无 |
| 2026-05-18 | 日志查询升级为真实 ES search | `log_query_service.py` | bool 查询、分页、结果转换 | 需 ELK 容器联调验证 |
| 2026-06-16 | M1 四模块真实 ES 实现 | `field_catalog.py` 等 | AC 全通过 | — |
| 2026-06-16 | **拆索引链路对齐**：Logstash 按 log_type 写入拆分索引；`field_catalog` 统一 web_server 索引 segment（下划线）；`aggregation_service` 移除单索引回退 | `field_catalog.py`、`aggregation_service.py`、`logstash/pipeline/logstash.conf`、本 DEV.md | 指定 log_types 的聚合 API 命中 `app-logs-{type}-*`；pytest 18 passed（field_catalog + aggregation） | `search_logs` 仍用全局 pattern；历史统一索引数据仍在 |
| 2026-06-23 | **真实 ES 联调修复聚合 bug**：`_terms_field` 原对所有字段补 `.keyword`，但索引模板将枚举字段直接映射为 `keyword`（仅 message/reason/change_summary 为 text+keyword 多字段），导致 `by_service` / `error_code` 分布 / `group_by` terms 聚合静默返回 0 桶；改为仅对多字段文本补 `.keyword`，其余原样返回 | `aggregation_service.py`、本 DEV.md | 真实 ES 验证：traffic.by_service、aggregate_errors、aggregate(group_by=service_name) 均正常返回桶 | — |
