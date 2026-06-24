# Services 模块 DEV 维护文档

## 1. 模块定位

`app/services/` 承载后端业务与外部系统访问逻辑。API 层只能调用 service，不应直接拼接 Elasticsearch 查询、直接创建 Kafka Producer、直接执行 Docker 查询，或把外部系统访问细节写进路由函数。

## 2. 当前服务边界

| 文件 / 目录 | 职责 | 状态 |
| --- | --- | --- |
| `app/services/elasticsearch/` | 客户端、日志查询、聚合、上下文、字段目录、索引模板、cluster health | M1 已实现 |
| `app/services/kafka/` | Kafka 消息生产、topic 预建、broker 探测 | 可用 |
| `app/services/diagnosis/` | 声明式规则（`rule_definitions`/`match_log`）、关键词分流、同步诊断门面 | M5 规则层已实现 |
| `app/services/simulation/` | 模拟日志生成（7 大类） | 可用，P1 增强 trace 链路 |
| `app/services/langchain/` | LLM 管理、Prompt、证据压缩、report/diagnosis Chain | M3 已实现；`relation_chain`/`alert_chain` 占位 |
| `app/services/analysis/` | LangGraph 定时/规则子图、scheduler、trigger_scanner | M4/M5 已实现；`graph_main` 占位（M6） |
| `app/services/tools/` | 10 个 LangChain StructuredTool + registry | M2 已实现；`create_mcp_server` 占位（M7） |
| `app/services/report/` | `analysis-results-*` 报告持久化 | M4 已实现 |
| `app/services/alert/` | `alerts-*` 预警持久化、去重、确认状态机 | M5 已实现 |
| `app/services/docker_status.py` | Docker Compose 容器状态只读查询；本地 Docker 不可用时按网关端口探测 Kafka/ES/Logstash/Kibana | 可用 |
| `app/services/pipeline_verification.py` | 全链路验证任务封装 | 可用 |

## 3. Docker 状态查询约定

- `docker_status.py` 只做只读查询，优先通过 Docker CLI 执行 `docker ps -a` 与 `docker stats --no-stream`。
- 查询范围由 `Settings.docker_project_name` 与 `Settings.docker_monitored_services` 控制，默认 project 为 `location`。
- 服务返回归一化状态：`running`、`down`、`unknown`。
- Docker CLI 不存在、Docker API 不可访问、权限不足，或本地 project 中缺少目标容器时，不抛出到 API 层；对 `kafka`、`elasticsearch`、`logstash`、`kibana` 使用 `config/gateway.yaml` 推导出的宿主机端口做 TCP 探测兜底。
- 网关探测端口：Kafka 使用 `settings.kafka_bootstrap_servers`；Elasticsearch 使用 `settings.elasticsearch_hosts`；Kibana 使用 `settings.kibana_base_url`；Logstash 使用同一网关宿主机的 `9600`。
- 不在该服务中启动、停止、删除或重启容器。

## 4. 模块状态表

| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/Agent | 风险等级 | 备注 |
| --- | --- | --- | --- | --- | --- |
| Services（整体） | M1～M5 主链路可用 | 2026-06-22 | elk-backend-agent | 中 | M6 主图、M7 MCP/关系发现待开发 |

## 5. 禁止重复实现清单

| 能力 | 正确位置 | 禁止行为 |
| --- | --- | --- |
| ES cluster health 探测 | `app/services/elasticsearch/cluster_status.py` | 禁止在 `app/api/v1/system.py` 直接创建 ES client |
| Kafka topic / broker 探测 | `app/services/kafka/cluster_status.py` | 禁止在 API 层直接创建 KafkaAdminClient |
| ES 聚合 DSL | `app/services/elasticsearch/aggregation_service.py` | 禁止在 analysis 层直接拼 DSL |
| LLM 调用 | `app/services/langchain/` | 禁止在 analysis 节点内直接调 OpenAI |
| 报告/预警写入 | `report/`、`alert/` | 禁止在 LangGraph 节点内直连 ES 索引 API |

## 6. 开发日志区

| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
| --- | --- | --- | --- | --- |
| 2026-05-13 | 增强系统配置快照探测服务 | `elasticsearch/cluster_status.py`、`kafka/cluster_status.py` | 为 `/system/status` 提供 ES/Kafka 只读探测 | — |
| 2026-05-14 | 日志生成与 Kafka 生产落地 | `simulation/`、`kafka/`、`tasks/run_log_producer.py` | 结构化日志写入 Kafka | — |
| 2026-05-18 | 新增全链路验证服务封装 | `pipeline_verification.py` | 四节点状态与终端输出 | 依赖基础设施在线 |
| 2026-06-16 | 按总体规划建立分域骨架 | `langchain/`、`analysis/`、`tools/`、`report/`、`alert/`、`elasticsearch/` 扩建 | 物理隔离，初期部分函数占位 | 已由 M1～M5 逐步替换为真实实现 |
| 2026-06-16 | **M1 收口**：ES 聚合/上下文/字段目录/索引模板 | `elasticsearch/*` | 六类聚合 + 四类上下文 + field_catalog | 见 `elasticsearch/DEV.md` |
| 2026-06-17 | **M2 收口**：10 工具 + registry | `tools/*` | StructuredTool 读写分离 | `create_mcp_server` 仍 M7 |
| 2026-06-22 | **M3 收口**：LangChain 双 Chain + 降级 | `langchain/*` | 22 测全绿 | `relation_chain`/`alert_chain` 占位 |
| 2026-06-22 | **M4 收口**：定时子图 + 报告持久化 | `analysis/graph_scheduled.py`、`scheduler.py`、`report/` | scheduler→write_report 闭环 | `graph_main` 仍 M6 |
| 2026-06-22 | **M5 收口**：规则子图 + 预警闭环 | `diagnosis/rule_*`、`analysis/graph_rule.py`、`trigger_scanner.py`、`alert/` | scan_once→子图→报告+预警 | 频率规则聚合待 P1 |
| 2026-06-22 | 同步 Services DEV 至 M5 现状 | `app/services/DEV.md` | 边界表、状态表、开发日志与里程碑对齐 | — |
| 2026-06-23 | 为 Docker 状态增加网关端口探测兜底 | `docker_status.py`、`app/services/DEV.md` | 小组成员本地后端即使没有本地 Docker 容器，也能按 `gateway.yaml` 探测远端 Kafka/ES/Logstash/Kibana 并返回 `gateway-*` 运行态；兜底探测异常会降级为单服务 `unknown`，不能打挂 `/system/status` | 网关探测只能确认端口可达，不返回远端容器 CPU/内存统计 |
