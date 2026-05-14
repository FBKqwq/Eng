# Core 模块 DEV 文档

## 1. 文档用途说明
本文档用于维护 `app/core/` 中的全局配置与基础能力，确保环境变量与设置项单一来源，避免各模块重复读取 `.env` 或硬编码连接串。

## 2. 项目模块总览
| 文件 | 主要职责 |
|---|---|
| `app/core/config.py` | Pydantic Settings：应用名、端口、Kafka、ES、日志生产间隔等 |

## 3. 模块职责边界
- 应该放在这里：全局配置、常量、日志/安全等横切基础（若后续增加）。
- 不应该放在这里：具体业务服务、API 路由、ES 查询、诊断规则。

## 4. 已实现功能清单
- 已提供 `Settings` 与单例 `settings`，支持 `.env` 加载与 `extra="ignore"`。
- Elasticsearch 可选认证：`elasticsearch_username`、`elasticsearch_password`；密码字段兼容环境变量 `ELASTICSEARCH_PASSWORD` 与 `ELASTIC_PASSWORD`。

## 5. 待开发功能清单（P0-P3）
- P0：为生产环境补充必填项校验（如 ES/Kafka 地址非空告警）。
- P1：区分 dev/staging/prod 的配置 profile 或前缀约定。
- P2：集中日志级别与格式配置。
- P3：密钥与敏感项从环境注入的说明与安全默认值策略。

## 6. 模块状态表
| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| Core | 稳定可用 | 2026-05-14 | codex | 低 | 含 ES 安全认证相关配置项，敏感值仅走环境注入 |

## 7. 禁止重复实现清单
| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| 环境变量与全局配置 | `app/core/config.py` | 禁止在 `services/` 或 `api/` 内重复定义同类 Settings 或直接读 os.environ 散落各处 |

## 8. 真实实现与设计愿景差异
| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 配置治理 | 全链路配置可审计、可分组、可文档化 | 当前为单文件基础字段 | 随模块增加拆分或补充文档字段说明 |

## 9. 开发日志区
| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-05-11 | 初始化 Core 模块 DEV 文档 | `app/core/DEV.md` | 建立配置模块维护基线 | 待新增 `core` 子文件时更新模块总览 |
| 2026-05-14 | 恢复被基础版本覆盖的 Docker 监控配置项 | `app/core/config.py` | `docker_project_name`、`docker_monitored_services` 重新可供系统状态接口读取 | 需重启后端进程后生效 |
| 2026-05-14 | 增加 Elasticsearch 用户名/密码配置项 | `app/core/config.py` | 与 `get_es_client` 的 `basic_auth` 对齐，兼容 `ELASTIC_PASSWORD` | 密钥不入库、不写入代码 |

## 2026-05-13 补充：Docker 监控配置

### 变更记录

| 日期 | 变更 | 涉及文件 | 说明 | 状态 |
| --- | --- | --- | --- | --- |
| 2026-05-13 | 新增 Docker 监控配置项 | `app/core/config.py` | 增加 `docker_project_name`、`docker_monitored_services`，用于控制开发者监控页查询的 Docker Compose 项目与服务集合 | 已验证 |

### 配置项

`Settings` 新增以下配置项，可通过 `.env` 覆盖：

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `docker_project_name` | `location` | Docker Compose project 名称，用于 `docker ps` label 过滤 |
| `docker_monitored_services` | `kafka,elasticsearch,logstash,kibana,setup` | 开发者监控页需要展示的服务列表 |

配置只影响后端状态查询范围，不负责启动、停止或编排容器。

## 2026-05-14 补充：Elasticsearch 安全认证配置

| 配置项 / 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| `elasticsearch_username` / `ELASTICSEARCH_USERNAME` | `elastic` | ES 启用安全时与密码一起用于客户端 `basic_auth` |
| `elasticsearch_password` / `ELASTICSEARCH_PASSWORD` | 空 | 非空时所有经 `get_es_client()` 的请求携带 Basic 认证 |
| `ELASTIC_PASSWORD` | — | 与 `ELASTICSEARCH_PASSWORD` 等价别名，便于与 Compose 对齐 |

说明：`app/services/elasticsearch/client.py` 在密码非空时优先采用进程环境中已设置的 `ELASTICSEARCH_*` / `ELASTIC_PASSWORD`（便于 task 在 import 之后 `load_dotenv`），否则使用 `Settings` 已加载字段。
