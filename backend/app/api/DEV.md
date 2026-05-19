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

## 3. 模块职责边界
- 应该放在这里：请求接收、基础校验、调用 service、统一响应返回。
- 不应该放在这里：Kafka/ES 直连代码、复杂业务规则、诊断核心算法。

## 4. 已实现功能清单
- 已提供 health/logs/diagnosis/system 四类 v1 接口文件。
- 已具备路由聚合入口文件。
- `POST /api/v1/system/pipeline/verify` 已接入后端全链路验证服务，返回节点状态与终端输出。

## 5. 待开发功能清单（P0-P3）
- P0：补齐接口错误码与异常返回结构一致性。
- P1：增加 metrics 类接口并接入服务层。
- P2：补充接口层参数校验与示例响应文档。
- P3：补充 API 访问审计日志与限流策略。

## 6. 模块状态表
| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| API | 可用但需完善 | 2026-05-18 | codex | 中 | `/api/v1/system/status` 与 `/api/v1/system/pipeline/verify` 已可供系统状态页使用 |

## 7. 禁止重复实现清单
| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| 日志查询逻辑 | `app/services/elasticsearch/` | 禁止在 `app/api/v1/logs.py` 直接拼 ES 查询 |
| 诊断规则引擎 | `app/services/diagnosis/rule_engine.py` | 禁止在 `app/api/v1/diagnosis.py` 重复写规则分流 |
| Kafka 生产逻辑 | `app/services/kafka/` | 禁止在 API 路由直接写 Kafka Producer |

## 8. 真实实现与设计愿景差异
| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 接口标准化 | 完整统一的请求响应与错误规范 | 已有接口但规范不完全统一 | 补齐通用响应模型和错误码映射 |

## 9. 开发日志区
| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-05-06 | 初始化 API 模块 DEV 文档 | `app/api/DEV.md` | 建立模块开发维护基线 | 待后续按实际开发持续更新 |
| 2026-05-14 | 日志查询路由与 schema 对齐：`LogSearchRequest` 更名为 `LogQueryRequest` | `app/api/v1/logs.py` | 修复启动期 ImportError，与 `app/schemas/log.py` 一致 | 无 |
| 2026-05-14 | 恢复被基础版本覆盖的系统状态接口 | `app/api/v1/system.py` | `/status` 重新返回 `kafka`、`elasticsearch`、`docker`、`containers`、`services`，并恢复 `/containers` | 需重启当前 8000 后端进程后浏览器才能命中新代码 |
| 2026-05-18 | 新增全链路验证 API | `app/api/v1/system.py` | `POST /system/pipeline/verify` 调用 service 执行 `verify_log_pipeline_full` 并返回结构化节点状态 | 验证耗时取决于 Kafka/Logstash/ES 当前状态 |
| 2026-05-19 | 全链路验证 API 支持多线程参数 | `app/api/v1/system.py` | `PipelineVerifyRequest.workers` 透传到验证 service，覆盖多线程生产验证 | workers 当前由 schema 限制在 1~8 |

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
