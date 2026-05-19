# Simulation 服务模块 DEV 文档

## 1. 文档用途说明
本文档用于维护 `app/services/simulation/` 下的日志模拟能力，确保日志生成逻辑集中、字段稳定，并能被 Kafka、Logstash、Elasticsearch、规则引擎与后续 LangGraph 诊断流程持续消费。

## 2. 项目模块总览
| 文件 | 主要职责 |
|---|---|
| `app/services/simulation/log_generator.py` | 生成结构化电商平台模拟日志，包括业务日志、行为埋点日志、性能日志、安全日志与基础设施日志 |

## 3. 模块职责边界
- 应该放在这里：日志事件生成、模拟行为编排、日志字段模板、异常场景模板、埋点字段补充。
- 不应该放在这里：Kafka 发送实现、HTTP 路由处理、Elasticsearch 查询逻辑、LangGraph 节点编排。
- 当前模块只负责构造可消费的日志 dict；发送由 `app/services/kafka/producer.py` 与 `app/tasks/run_log_producer.py` 负责。

## 4. 已实现功能清单
- 已生成统一公共字段：`timestamp`、`log_id`、`log_level`、`log_type`、`event_type`、`service_name`、`trace_id`、`span_id`、`request_id`、`user_id`、`session_id`、`client_ip`、`status`、`tags`、`extra`。
- 已支持普通电商平台业务日志：浏览、搜索、下单、库存校验、支付等应用日志。
- 已支持电商平台埋点日志：页面访问、商品点击、搜索词、加购、下单按钮、支付按钮、推荐位点击等行为事件。
- 埋点日志已包含 `tracking` 对象，记录 `event_count`、`click_count`、`page_view_count`、`unique_visitor_count`、`dwell_time_ms`、`bounce`、`conversion_step`。
- 已支持异常分析字段：`error_code`、`exception_type`、`response_time_ms`、`downstream_service`、`retry_count`、`anomaly_signal`、`diagnosis_hints`。
- 已支持辅助上下文字段：性能指标、安全拦截、Kafka/Elasticsearch/Logstash/Backend 基础设施健康日志。
- 已支持 Nginx 风格 Web Server 日志：`log_type=web_server`，覆盖 access/error log、request line、remote addr、status、body bytes、referer、user agent、request_time、upstream_*、TLS 等字段。

## 5. 待开发功能清单（P0-P3）
- P0：接通 Kafka -> Logstash -> Elasticsearch 后，确认字段映射与索引模板完全兼容。
- P1：为同一 `trace_id` 生成多条连续链路日志，覆盖网关、订单、库存、支付等调用顺序。
- P1：增加可配置异常比例、流量比例、热点商品和高峰时段参数。
- P2：提供批量生成和固定随机种子能力，便于压测与演示复现。
- P3：引入更细的营销、优惠券、售后、退款等电商场景。

## 6. 模块状态表
| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/Agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| Simulation Service | 可用但需继续增强 | 2026-05-19 | codex | 中 | 已覆盖应用、行为、Web Server、性能、安全、基础设施日志；模拟日志 `timestamp` 统一输出 UTC `Z` 时间；多线程发送由 task 层负责 |

## 7. 禁止重复实现清单
| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| 日志模拟与模板生成 | `app/services/simulation/` | 禁止在 `tasks/` 或 `api/` 中重复写事件模板 |
| Kafka 消息发送 | `app/services/kafka/producer.py` | 禁止在 simulation 模块直接初始化 Kafka Producer |
| 日志查询与聚合 | `app/services/elasticsearch/` | 禁止在 simulation 模块查询 ES |
| 诊断编排 | `app/services/diagnosis/` | 禁止在 simulation 模块实现 LangGraph 流程 |

## 8. 真实实现与设计愿景差异
| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 结构化日志生成 | 覆盖行为、应用、Web Server、性能、安全、基础设施等多类日志 | 已实现单条随机日志生成并包含 Nginx Web Server 日志 | 后续增加同一 trace 的连续链路批量生成 |
| 埋点日志 | 支持点击量、访问量、停留时长、转化步骤等指标 | 已在 behavior 日志中加入 tracking 对象 | 后续接入 ES 聚合与前端指标展示 |
| LangGraph 诊断上下文 | 日志天然携带根因分析所需证据 | 已增加 anomaly_signal 与 diagnosis_hints | 后续由诊断服务检索并组装图式分析上下文 |
| 基础设施闭环 | Kafka/Logstash/ES 全链路消费模拟日志 | 当前仅后端生成与 Kafka Producer 侧可发送 | 需要基础设施层补 Kafka input 与索引 mapping |

## 9. 开发日志区
| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-05-06 | 初始化 Simulation 模块 DEV 文档 | `app/services/simulation/DEV.md` | 建立模拟模块维护基线 | 待补充模板维度与参数化能力 |
| 2026-05-13 | 扩展电商平台结构化日志生成，新增埋点日志、异常诊断上下文、性能/安全/基础设施辅助日志 | `app/services/simulation/log_generator.py`、`app/services/simulation/DEV.md` | 生成日志已能覆盖点击量、访问量、业务异常和 LangGraph 诊断上下文 | Kafka -> Logstash -> ES 链路与索引 mapping 仍需基础设施支持验证 |
| 2026-05-19 | 新增 Nginx Web Server 日志生成 | `app/services/simulation/log_generator.py`、`tests/test_health.py` | `build_mock_log()` 可随机产出 `web_server` 类型日志，字段符合 schema 中 Nginx access/error 契约 | 后续可按固定比例或指定类型生成 |
| 2026-05-19 | 修复模拟日志时区解析问题 | `app/services/simulation/log_generator.py`、`app/services/simulation/DEV.md` | `timestamp` 改为 UTC ISO-8601 `Z` 格式，避免 Kibana `Last 15 minutes` 因本地无时区时间被 ES 当成 UTC 而查询不到；Nginx `time_local` 输出本地时区偏移 | 旧索引中已写入的历史文档不会自动修正，需要重新生成新日志观察 |
