# Kafka 服务模块 DEV 文档

## 1. 文档用途说明
本文档用于维护 `app/services/kafka/` 的开发边界、实现状态与迭代记录，确保日志生产链路能力集中实现，不在其他层重复造轮子。

## 2. 项目模块总览
| 文件 | 主要职责 |
|---|---|
| `app/services/kafka/producer.py` | 生产日志消息到 Kafka Topic，支持复用 Producer 与 topic 覆盖 |
| `app/services/kafka/topic_setup.py` | 启动前预建配置中的业务 topic（与 compose 单副本环境默认 RF=1 对齐） |
| `app/services/kafka/cluster_status.py` | 只读 AdminClient 状态快照，供系统状态接口使用 |

## 3. 模块职责边界
- 应该放在这里：Kafka Producer 封装、发送重试策略、消息结构适配。
- 不应该放在这里：HTTP 路由处理、ES 查询逻辑、诊断推理流程。

## 4. 已实现功能清单
- 已有 Kafka producer 服务文件。
- `send_log_message` 支持传入复用 `KafkaProducer`、可选 `topic` 覆盖；失败时抛出带 bootstrap/topic 信息的 `RuntimeError`。
- `ensure_configured_topic()`：在 broker 可达时确保 `settings.kafka_topic` 存在（默认 3 分区、副本因子 1）。
- 多线程生产由 `app/tasks/run_log_producer.py --workers` 编排；Kafka service 继续只负责单 Producer 连接与发送封装。

## 5. 待开发功能清单（P0-P3）
- P0：与 Logstash Kafka input 接通后做端到端发送抽样验证。
- P1：发送指标统计与更细粒度重试/退避策略。
- P2：支持批量发送与吞吐优化。
- P3：引入可观测性埋点与告警钩子。

## 6. 模块状态表
| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| Kafka Service | 可用但需完善 | 2026-05-19 | codex | 中 | topic 预建、producer 复用与快照探测并存；task 层已验证多线程统一写入 topic |

## 7. 禁止重复实现清单
| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| Kafka 消息生产 | `app/services/kafka/` | 禁止在 `tasks/`、`api/` 或 `simulation/` 直接散写 Producer 连接代码 |

## 8. 真实实现与设计愿景差异
| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 稳定日志生产 | 可观测、可重试、可追踪的生产服务 | 当前能力基础可用 | 增强重试、指标与异常可诊断性 |

## 9. 开发日志区
| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-05-06 | 初始化 Kafka 模块 DEV 文档 | `app/services/kafka/DEV.md` | 建立模块维护基线 | 待结合真实运行结果持续更新 |

## 2026-05-13 补充：Kafka 状态快照

### 模块状态表更新

| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
| --- | --- | --- | --- | --- | --- |
| Kafka Service | 可用但需完善 | 2026-05-14 | codex | 中 | 已补充 topic 预建与 producer 复用发送；待 Logstash 侧消费验证 |

### 已实现功能清单更新

- `get_kafka_status_snapshot()`：读取 broker/topic 基础信息，并描述配置 topic 的分区数与副本数。
- Kafka 不可达时返回 `available=false` 和 `error`，保证系统状态接口稳定返回。

### 开发日志区

| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
| --- | --- | --- | --- | --- |
| 2026-05-13 | 新增 Kafka 状态快照 | `app/services/kafka/cluster_status.py`、`app/schemas/system.py` | `/system/status` 可展示 Kafka broker/topic 数量、配置 topic 是否存在、分区数和副本数 | 依赖 Kafka broker 真实可访问 |
| 2026-05-14 | 日志生产落地：topic 预建、producer 复用与发送错误信息 | `topic_setup.py`、`producer.py` | `run_log_producer` 启动可确保 `app-logs`；发送失败可诊断 | 单 broker 环境副本因子固定为 1 |
| 2026-05-19 | 多线程生产能力完成联调 | `app/tasks/run_log_producer.py` | 3 个 worker 可并发生成日志并统一写入 `app-logs` | Kafka service 本身保持轻量封装，不承担线程调度 |
