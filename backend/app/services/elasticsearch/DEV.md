# Elasticsearch 服务模块 DEV 文档

## 1. 文档用途说明
本文档用于维护 `app/services/elasticsearch/` 的实现状态和边界，确保日志查询、索引访问与 ES 客户端能力集中治理，避免接口层和其他服务越层操作 ES。

## 2. 项目模块总览
| 文件 | 主要职责 |
|---|---|
| `app/services/elasticsearch/client.py` | Elasticsearch 客户端封装 |
| `app/services/elasticsearch/log_query_service.py` | 日志查询与聚合服务 |

## 3. 模块职责边界
- 应该放在这里：ES 客户端连接、查询构建、结果转换。
- 不应该放在这里：HTTP 参数处理、诊断规则分流、Kafka 生产逻辑。

## 4. 已实现功能清单
- 已有 ES 客户端与日志查询服务文件。
- `get_es_client()`：在配置非空密码时通过 `basic_auth` 连接 ES，兼容无安全认证的本地开发。

## 5. 待开发功能清单（P0-P3）
- P0：确认查询链路真实可用并处理连接异常（含启用安全认证时的账号配置）。
- P1：补齐聚合查询与时间窗口统计能力。
- P2：统一查询参数映射与分页排序策略。
- P3：缓存热门查询与慢查询诊断能力。

## 6. 模块状态表
| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| Elasticsearch Service | 稳定可用 | 2026-05-14 | codex | 低 | cluster health 与后续真实查询共用带认证的客户端 |

## 7. 禁止重复实现清单
| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| ES 查询构建 | `app/services/elasticsearch/` | 禁止在 `api/v1/logs.py` 直接拼 DSL |
| ES 客户端连接 | `app/services/elasticsearch/client.py` | 禁止在多个模块重复初始化客户端 |

## 8. 真实实现与设计愿景差异
| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 高可用日志查询 | 结构化、高性能、可扩展查询能力 | 已有基础查询实现 | 逐步补齐聚合、性能与容错 |

## 9. 开发日志区
| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-05-06 | 初始化 Elasticsearch 模块 DEV 文档 | `app/services/elasticsearch/DEV.md` | 建立查询模块维护基线 | 待补充真实压测与异常数据记录 |
| 2026-05-14 | 日志查询入参类型与 `LogQueryRequest` 对齐 | `app/services/elasticsearch/log_query_service.py` | 应用可正常 import，占位查询逻辑不变 | 无 |

## 2026-05-13 补充：Cluster Health 快照

### 模块状态表更新

| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
| --- | --- | --- | --- | --- | --- |
| Elasticsearch Service | 稳定可用 | 2026-05-14 | codex | 低 | cluster health 与后续真实查询共用带认证的客户端 |

### 已实现功能清单更新

- `get_elasticsearch_health_snapshot()`：读取 ES `info`、`cluster.health` 和 index pattern `count`，返回结构化健康快照。
- 外部连接失败时返回 `available=false`、`cluster_status=unknown` 和 `error`，保证系统状态接口稳定返回。

### 开发日志区

| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
| --- | --- | --- | --- | --- |
| 2026-05-13 | 新增 ES 集群健康快照 | `app/services/elasticsearch/cluster_status.py`、`app/schemas/system.py` | `/system/status` 可展示 `cluster_status`（green/yellow/red/unknown）、节点、分片与文档计数 | 依赖 Elasticsearch 服务真实可访问 |
| 2026-05-14 | ES 客户端增加 `basic_auth`（用户名/密码来自 `Settings` 与环境变量回退） | `app/services/elasticsearch/client.py` | 监控页 cluster health 在 ES 启用安全时可正常拉取 | 无 |
| 2026-05-14 | 日志查询服务入参类型与 schema 对齐 | `app/services/elasticsearch/log_query_service.py` | `search_logs` 使用 `LogQueryRequest`，消除错误导入 | 无 |
| 2026-05-14 | `get_es_client` 对账号密码去外层引号并统一 env 回退顺序 | `app/services/elasticsearch/client.py` | 修复 `.env` 中 `ELASTICSEARCH_PASSWORD='changeme'` 导致全链路脚本 ES 检索始终为空 | 无 |
