# Services 模块 DEV 维护文档

## 1. 模块定位

`app/services/` 承载后端业务与外部系统访问逻辑。API 层只能调用 service，不应直接拼接 Elasticsearch 查询、直接创建 Kafka Producer、直接执行 Docker 查询，或把外部系统访问细节写进路由函数。

## 2. 当前服务边界

| 文件 / 目录 | 职责 |
| --- | --- |
| `app/services/elasticsearch/` | Elasticsearch 客户端与日志查询服务 |
| `app/services/kafka/` | Kafka 消息生产服务 |
| `app/services/diagnosis/` | 规则优先的智能诊断分析服务 |
| `app/services/simulation/` | 模拟日志生成 |
| `app/services/docker_status.py` | Docker Compose 容器状态只读查询服务 |

## 3. Docker 状态查询约定

- `docker_status.py` 只做只读查询，当前通过 Docker CLI 执行 `docker ps -a` 与 `docker stats --no-stream`。
- 查询范围由 `Settings.docker_project_name` 与 `Settings.docker_monitored_services` 控制，默认 project 为 `location`。
- 服务返回归一化状态：`running`、`down`、`unknown`。
- Docker CLI 不存在、Docker API 不可访问或权限不足时，不抛出到 API 层；返回 `available=false`、`error` 和各服务 `unknown` 状态。
- 不在该服务中启动、停止、删除或重启容器。

## 4. 维护记录

| 日期 | 变更 | 涉及文件 | 说明 | 状态 |
| --- | --- | --- | --- | --- |
| 2026-05-13 | 新增 Docker 容器状态查询服务 | `app/services/docker_status.py` | 为开发者监控页提供 Kafka、Elasticsearch、Logstash、Kibana、setup 容器运行态与 CPU/内存等快照 | 已验证 |

## 2026-05-13 补充：系统配置快照服务边界

### 模块状态表更新

| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
| --- | --- | --- | --- | --- | --- |
| Services | 可用但需完善 | 2026-05-13 | codex | 中 | 新增 Kafka / Elasticsearch 只读状态探测；外部依赖不可达时返回结构化不可用状态，不向 API 层抛出 |

### 禁止重复实现清单更新

| 能力 | 正确位置 | 禁止行为 |
| --- | --- | --- |
| ES cluster health 探测 | `app/services/elasticsearch/cluster_status.py` | 禁止在 `app/api/v1/system.py` 直接创建 ES client 或调用 cluster API |
| Kafka topic / broker 探测 | `app/services/kafka/cluster_status.py` | 禁止在 `app/api/v1/system.py` 直接创建 KafkaAdminClient |

### 开发日志区

| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
| --- | --- | --- | --- | --- |
| 2026-05-13 | 增强系统配置快照探测服务 | `app/services/elasticsearch/cluster_status.py`、`app/services/kafka/cluster_status.py` | 为 `/system/status` 提供 ES cluster health 与 Kafka topic/broker 只读探测 | 已通过 compileall 与 TestClient 验证 |
| 2026-05-14 | 日志生成与 Kafka 生产落地 | `simulation/log_generator.py`、`kafka/producer.py`、`kafka/topic_setup.py`、`tasks/run_log_producer.py` | 结构化日志写入 Kafka，任务启动预建 topic | Logstash Kafka input 待配置 |
| 2026-05-14 | 任务层增加 Kafka 消费侧自证脚本 | `tasks/verify_log_kafka_pipeline.py` | 内置 consumer 校验 log_id 闭环 | 与 Logstash 无关，仅 broker 内验证 |
