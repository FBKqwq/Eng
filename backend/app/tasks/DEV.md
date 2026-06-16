# Tasks 模块 DEV 文档

## 1. 文档用途说明

本文档用于维护 `app/tasks/` 下可独立运行的脚本任务，明确其与 `services/` 的调用关系，避免在任务脚本中堆积本属于服务层的业务实现。所有 Agent 在继续开发前应先阅读，并在完成开发后同步更新「模块状态表」和「开发日志区」。

## 2. 项目模块总览

| 文件 | 主要职责 |
|---|---|
| `app/tasks/run_log_producer.py` | 循环生成模拟日志并通过 Kafka producer 发送 |
| `app/tasks/verify_log_kafka_pipeline.py` | 一次性验证：日志生成 → producer → topic → 内置 consumer 消费并比对 log_id |
| `app/tasks/verify_log_pipeline_full.py` | 全链路验证：生成 → Kafka → 脚本消费 Kafka → Logstash → ES 检索（含 @timestamp/tags） |
| `app/tasks/init_indices.py` | **M1 新增**：调用 `index_service.init_all_indices` / `verify_templates` 初始化或校验 ES 索引模板 |
| `app/tasks/run_mcp_server.py` | **占位** 独立运行 MCP Server（M7） |

## 3. 模块职责边界

- 应该放在这里：CLI/脚本入口、调度循环、进程级参数、组合调用已有 service。
- 不应该放在这里：重复实现 `log_generator` 或 `producer` 内部协议、HTTP 接口、schema 定义、ES 模板 DSL（应下沉至 `index_service`）。
- `init_indices.py` 仅 import 调用 `index_service`，不得在此文件内实现 mapping 或 `get_es_client` 逻辑。

## 4. 已实现功能清单

### 日志生产与链路验证

- 已实现基于 `settings.log_producer_interval_seconds` 的定时发送循环（可用 `--interval` 覆盖）。
- 已组合 `build_mock_log` 与 `send_log_message`，循环内复用单个 `KafkaProducer`。
- 启动时默认调用 `ensure_configured_topic()` 预建业务 topic，可用 `--skip-ensure-topic` 跳过。
- 启动失败（topic 预建或 producer 连接）时向 stderr 输出可诊断中文提示并带退出码。
- 支持 `--count`、`--topic`、`--workers` 命令行参数。
- `verify_log_kafka_pipeline.py`：先发后收，用独立 consumer group 与 `latest` 偏移证明 producer 写入可被消费。
- `verify_log_pipeline_full.py`：分段打印各环产出；Kafka 内校验后轮询 ES；支持 `--workers` 多线程生成。

### init_indices.py（M1-03）

**启动命令**

```bash
# 在 location/backend 目录下执行
python -m app.tasks.init_indices
```

**可选参数**

| 参数 | 说明 |
|---|---|
| `--verify-only` | 仅调用 `verify_templates()` 校验模板是否存在，不创建 |
| `--json` | 额外在 stdout 输出完整 JSON 结果 |

**行为说明**

- 默认模式：依次调用 `index_service.init_all_indices()`，创建 component 模板、index 模板与分析索引模板。
- `--verify-only` 模式：只读检查关键模板是否已存在，缺失时 stderr 列出模板名并以退出码 1 结束。
- ES 不可达或权限不足时，打印结构化中文摘要并以退出码 1 结束（不抛未捕获异常）。
- 支持幂等执行：重复运行不会破坏已有模板（ES put template 语义）。
- 依赖：ES 服务可访问且账号具备索引模板管理权限；否则走「结构化失败」路径。

**示例**

```bash
# 首次部署或本地联调：创建全部索引模板
python -m app.tasks.init_indices

# 仅校验模板是否就绪（CI / 冒烟）
python -m app.tasks.init_indices --verify-only

# 输出机器可读 JSON（便于脚本解析）
python -m app.tasks.init_indices --json
python -m app.tasks.init_indices --verify-only --json
```

## 5. 待开发功能清单（P0-P3）

- P1：支持从环境变量或配置文件读取发送 TPS 上限。
- P2：优雅退出与发送计数指标打印。
- P2：`verify_log_pipeline_full.py` 可选增强：除 `app-logs-*` 外校验拆分索引（如 `app-logs-application-*`）命中。
- P3：与容器/运维脚本对齐的 health 自检子命令。
- P3：`run_mcp_server.py` 真实 MCP 接入（M7）。

> P0「与 ES 索引模板对齐」已由 M1-03 + M1-02 完成；Logstash 已于 2026-06-16 按 `log_type` 拆分写入（见 `location/logstash/pipeline/logstash.conf`）。

## 6. 模块状态表

| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/Agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| run_log_producer | 稳定可用 | 2026-05-19 | codex | 低 | 支持多线程生产 |
| verify_log_kafka_pipeline | 稳定可用 | 2026-05-14 | codex | 低 | 依赖本机 Kafka |
| verify_log_pipeline_full | 稳定可用 | 2026-05-19 | codex | 低 | 需 Kafka + Logstash + ES |
| init_indices | M1 已完成 | 2026-06-16 | elk-backend-agent (M1-03) | 低 | 真实调用 index_service；需 ES 管理权限 |
| run_mcp_server | 占位 | 2026-06-16 | elk-backend-agent | 高 | 待 M7 接入 FastMCP |

## 7. 禁止重复实现清单

| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| 模拟日志构造 | `app/services/simulation/log_generator.py` | 禁止在验证脚本中复制生成模板 |
| Kafka 发送 | `app/services/kafka/producer.py` | 禁止在任务中手写另一套 Producer 序列化协议 |
| ES 索引模板 DSL | `app/services/elasticsearch/index_service.py` | 禁止在 `init_indices.py` 内实现 mapping 或直连 ES 模板 API |
| 链路验证消费 | `app/tasks/verify_log_kafka_pipeline.py` | 仅允许只读消费与 log_id 校验 |
| 全链路验证 | `app/tasks/verify_log_pipeline_full.py` | 仅只读查询 ES |

## 8. 真实实现与设计愿景差异

| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 可运维任务集 | 初始化索引、压测、链路探测统一入口与文档 | 日志生产 + 三路验证 + init_indices 已落地 | 按里程碑增量增加 task 并更新本文档 |
| 索引初始化 | 部署前一键创建拆分索引模板 | `init_indices` 真实调用 `index_service` | 已与 Logstash 拆分写入联调通过 |

## 9. 开发日志区

| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-05-11 | 初始化 Tasks 模块 DEV 文档 | `DEV.md` | 建立任务脚本维护基线 | — |
| 2026-05-14 | 日志生产任务落地 | `run_log_producer.py` | `python -m app.tasks.run_log_producer --count N` 可批跑 | 已与 Logstash Kafka 链路对齐 |
| 2026-05-14 | 新增 Kafka 链路验证脚本 | `verify_log_kafka_pipeline.py` | 可证明发送可被消费 | 依赖本机 Kafka |
| 2026-05-14 | 新增全链路验证脚本 | `verify_log_pipeline_full.py` | 验证至 ES 命中 | 需 Kafka、Logstash、ES |
| 2026-05-19 | 多线程生产支持 | `run_log_producer.py`、`verify_log_pipeline_full.py` | `--workers` 验证通过 | 可补 TPS 统计 |
| 2026-06-16 | 新增 MCP Server 占位任务 | `run_mcp_server.py` | 打印占位提示后退出 | 待 M7 |
| 2026-06-16 | **M1-03**：新增 `init_indices.py` CLI | `init_indices.py`、`DEV.md` | 支持 `python -m app.tasks.init_indices` 及 `--verify-only` / `--json` | ES 无管理权限时结构化失败 |
| 2026-06-16 | **Logstash 拆索引写入**：Kafka 日志按 `log_type` 路由至 `app-logs-{log_type}-YYYY.MM.dd` | `location/logstash/pipeline/logstash.conf`、本 DEV.md | 与 `index_service` / `field_catalog` 索引命名一致（`web_server` 保留下划线）；验收 30 条日志写入 5 个拆分索引 | `verify_log_pipeline_full` 仍默认查 `app-logs-*` 通配 |
