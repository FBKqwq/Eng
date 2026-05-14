# Tasks 模块 DEV 文档

## 1. 文档用途说明
本文档用于维护 `app/tasks/` 下可独立运行的脚本任务，明确其与 `services/` 的调用关系，避免在任务脚本中堆积本属于服务层的业务实现。

## 2. 项目模块总览
| 文件 | 主要职责 |
|---|---|
| `app/tasks/run_log_producer.py` | 循环生成模拟日志并通过 Kafka producer 发送 |
| `app/tasks/verify_log_kafka_pipeline.py` | 一次性验证：日志生成 -> producer -> topic -> 内置 consumer 消费并比对 log_id |
| `app/tasks/verify_log_pipeline_full.py` | 全链路验证：生成 -> Kafka -> 脚本消费 Kafka -> Logstash -> ES 检索（含 @timestamp/tags） |

## 3. 模块职责边界
- 应该放在这里：CLI/脚本入口、调度循环、进程级参数、组合调用已有 service。
- 不应该放在这里：重复实现 `log_generator` 或 `producer` 内部协议、HTTP 接口、schema 定义。

## 4. 已实现功能清单
- 已实现基于 `settings.log_producer_interval_seconds` 的定时发送循环（可用 `--interval` 覆盖）。
- 已组合 `build_mock_log` 与 `send_log_message`，循环内复用单个 `KafkaProducer`。
- 启动时默认调用 `ensure_configured_topic()` 预建业务 topic，可用 `--skip-ensure-topic` 跳过。
- 启动失败（topic 预建或 producer 连接）时向 stderr 输出可诊断中文提示并带退出码。
- 支持 `--count`、`--topic` 命令行参数。
- `verify_log_kafka_pipeline.py`：先发后收，用独立 consumer group 与 `latest` 偏移证明 producer 写入可被消费。
- `verify_log_pipeline_full.py`：分段打印各环产出；Kafka 内校验后轮询 ES（`ELASTIC_PASSWORD` 等从 `location/.env` 或 `backend/.env` 加载）。

## 5. 待开发功能清单（P0-P3）
- P0：与 ES 索引模板 / ILM 对齐（当前由 Logstash 写入 `app-logs-*`，字段映射可在索引模板中固化）。
- P1：支持从环境变量或配置文件读取发送 TPS 上限。
- P2：优雅退出与发送计数指标打印。
- P3：与容器/运维脚本对齐的 health 自检子命令。

## 6. 模块状态表
| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| Tasks | 可用但需完善 | 2026-05-14 | codex | 低 | Kafka→Logstash→ES 已由基础设施配置；任务脚本与 README 5.7 对齐 |

## 7. 禁止重复实现清单
| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| 模拟日志构造 | `app/services/simulation/log_generator.py` | 禁止在验证脚本中复制生成模板 |
| Kafka 发送 | `app/services/kafka/producer.py` | 禁止在任务中手写另一套 Producer 序列化协议 |
| 链路验证消费 | `app/tasks/verify_log_kafka_pipeline.py` | 仅允许只读消费与 log_id 校验，禁止写入业务逻辑 |
| 全链路验证 | `app/tasks/verify_log_pipeline_full.py` | 仅只读查询 ES；禁止在脚本内实现 Logstash 或 ES 写入逻辑 |

## 8. 真实实现与设计愿景差异
| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 可运维任务集 | 多任务（初始化索引、压测、链路探测）统一入口与文档 | 当前以日志生产为主，已增强 CLI | 按业务需要增量增加 task 并更新本文档 |

## 9. 开发日志区
| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-05-11 | 初始化 Tasks 模块 DEV 文档 | `app/tasks/DEV.md` | 建立任务脚本维护基线 | 待新增任务文件时补充模块总览表 |
| 2026-05-14 | 日志生产任务落地：topic 预建、producer 复用、CLI 与错误退出码 | `run_log_producer.py` | `python -m app.tasks.run_log_producer --count N` 可批跑 | 已与 Logstash Kafka 链路对齐，见 README 5.7 |
| 2026-05-14 | 新增 Kafka 链路验证脚本（内置 consumer） | `verify_log_kafka_pipeline.py`、`DEV.md` | `python -m app.tasks.verify_log_kafka_pipeline` 可证明发送可被消费 | 依赖本机 Kafka；Windows 终端建议 UTF-8 |
| 2026-05-14 | 基础设施侧接通 Logstash Kafka input | `location/docker-compose.yml`、`location/logstash/pipeline/logstash.conf`、`location/README.md` | 双 listener + `kafka:29092` 消费 `app-logs` 写入 `app-logs-*` | 详见 README 5.7 冒烟与 ES 认证方式 |
| 2026-05-14 | 新增全链路验证脚本（含 ES 轮询） | `verify_log_pipeline_full.py`、`DEV.md` | `python -m app.tasks.verify_log_pipeline_full` 验证至 ES 命中 | 需 Kafka、Logstash、ES 可用；ES 密码见 location/.env |
