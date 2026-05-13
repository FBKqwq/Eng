# 应用装配模块 DEV 文档

## 1. 文档用途说明
本文档用于说明 FastAPI 应用入口与路由装配职责（`app/main.py` 及根级装配相关变更），与 `app/api/` 区分：本模块只做应用创建与挂载，不承担具体业务接口实现。

## 2. 项目模块总览
| 文件 | 主要职责 |
|---|---|
| `app/main.py` | `create_app`、挂载 `api_router`、根路径探活响应 |

## 3. 模块职责边界
- 应该放在这里：FastAPI 实例创建、全局中间件（若增加）、路由前缀挂载、根健康信息。
- 不应该放在这里：具体 v1 业务路由实现、service 调用、schema 定义。

## 4. 已实现功能清单
- 已挂载 `api_router` 到 `/api` 前缀。
- 已暴露 `/` 根路径返回应用名与环境信息。

## 5. 待开发功能清单（P0-P3）
- P0：统一全局异常处理器（若项目约定需要）。
- P1：CORS、可信代理、请求 ID 中间件（按前端联调需求）。
- P2：OpenAPI 描述与标签整理。
- P3：启动生命周期事件（预热 ES 客户端等，需谨慎避免阻塞）。

## 6. 模块状态表
| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| App Bootstrap | 稳定可用 | 2026-05-11 | codex | 低 | 骨架清晰，扩展以中间件为主 |

## 7. 禁止重复实现清单
| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| 业务 API 实现 | `app/api/v1/*.py` | 禁止在 `main.py` 堆叠业务路由与业务逻辑 |

## 8. 真实实现与设计愿景差异
| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 生产级应用壳 | 中间件、观测、错误格式与部署一致 | 当前为最小骨架 | 按 P0-P1 逐步增加横切能力 |

## 9. 开发日志区
| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-05-11 | 初始化应用装配 DEV 文档 | `app/DEV.md` | 建立入口层维护基线 | 若仅改 `main.py` 请同步更新本文档日志 |

## 2026-05-13 补充：开发者容器状态监控后端能力

### 变更记录

| 日期 | 变更 | 涉及文件 | 说明 | 状态 |
| --- | --- | --- | --- | --- |
| 2026-05-13 | 新增开发者容器状态监控后端能力 | `app/api/v1/system.py`、`app/schemas/system.py`、`app/services/docker_status.py`、`app/core/config.py` | 后端通过只读 Docker CLI 查询 `location` compose 项目容器状态，为前端开发者监控页提供 Kafka、Elasticsearch、Logstash、Kibana、setup 的运行态和资源快照 | 已验证 |

### 接入说明

- 综合接口：`GET /api/v1/system/status`。
- 容器状态接口：`GET /api/v1/system/containers`。
- 查询服务：`app/services/docker_status.py`。
- 响应 schema：`app/schemas/system.py`。
- 配置项：`docker_project_name`、`docker_monitored_services`。

后端只查询容器状态，不执行启动、停止、删除、重启等 Docker 写操作。
