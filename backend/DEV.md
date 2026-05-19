# Backend DEV 文档

## 1. 文档用途

本文档是 `location/backend/` 目录级维护基线，用于说明后端当前真实状态、模块边界、接口契约、启动方式和开发注意事项。具体模块的细节以 `app/**/DEV.md` 为准；若本文档与模块文档冲突，优先以更靠近代码的模块文档为准，并在后续维护时同步修正。

## 2. 后端定位

后端是 ELK + Kafka + LangGraph 电商日志分析项目的业务 API 层，职责包括：

- 为前端提供健康检查、日志查询、智能诊断、系统状态接口。
- 读取 Kafka、Elasticsearch、Docker 容器状态并返回结构化结果。
- 组织日志查询、规则诊断、模拟日志生产等服务层能力。
- 通过 CORS 支持本地前端 `localhost:5173`、`127.0.0.1:5173` 等开发源访问。

后端不负责启动或停止 Kafka、Elasticsearch、Logstash、Kibana 容器；这些基础设施由 `location/docker-compose.yml` 管理。

## 3. 技术栈

| 类别 | 当前选型 |
| --- | --- |
| Web 框架 | FastAPI |
| ASGI 服务 | Uvicorn |
| 配置 | pydantic-settings，读取 `.env` |
| Kafka | kafka-python |
| Elasticsearch | elasticsearch Python client |
| 测试/联调 | FastAPI TestClient、curl、compileall |

## 4. 目录职责

| 路径 | 职责 |
| --- | --- |
| `app/main.py` | 创建 FastAPI app，挂载 CORS 和 `api_router` |
| `app/core/config.py` | 全局配置，包括 Kafka、ES、Docker 监控配置 |
| `app/api/router.py` | v1 路由聚合，挂载到 `/api` |
| `app/api/v1/*.py` | API 路由层，只接请求、调 service、返回 schema |
| `app/schemas/*.py` | 请求/响应数据契约 |
| `app/services/docker_status.py` | 只读 Docker CLI 容器状态查询 |
| `app/services/kafka/` | Kafka 生产与 broker/topic 状态探测 |
| `app/services/elasticsearch/` | ES client、日志查询、cluster health 探测 |
| `app/services/diagnosis/` | 规则分流与诊断能力 |
| `app/services/simulation/` | 模拟电商日志生成 |
| `app/tasks/` | 独立运行脚本 |
| `tests/` | 后端测试 |

## 5. 已实现接口

所有 API 统一挂载在 `/api` 前缀下。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/health` | 后端健康检查，返回 `{ "status": "ok" }` |
| GET | `/api/v1/system/status` | 系统状态综合快照 |
| GET | `/api/v1/system/containers` | Docker 容器状态快照 |
| GET/POST | `/api/v1/logs/*` | 日志查询相关接口 |
| POST | `/api/v1/diagnosis` | 智能诊断入口 |

### `/api/v1/system/status` 当前契约

该接口必须返回以下顶层字段，供前端系统状态页直接消费：

- `kafka_bootstrap_servers`
- `kafka_topic`
- `elasticsearch_hosts`
- `elasticsearch_index_pattern`
- `kafka`
- `elasticsearch`
- `docker`
- `containers`
- `services`

其中：

- `containers` 和 `services` 都是按服务名聚合的容器状态映射，当前包含 `kafka`、`elasticsearch`、`logstash`、`kibana`、`setup`。
- `docker.available=false` 时接口仍应稳定返回，容器项可以是 `unknown`。
- Elasticsearch cluster health 在 ES 未启用认证或已在 `.env` 中配置 `ELASTICSEARCH_PASSWORD` / `ELASTIC_PASSWORD` 时返回分片级详情；若仍失败则不代表容器未运行，前端会以 Docker 容器状态兜底展示。

## 6. CORS 规则

`app/main.py` 已配置 `CORSMiddleware`，允许本地开发源：

- `http://localhost:<port>`
- `http://127.0.0.1:<port>`
- `http://0.0.0.0:<port>`
- `http://[::1]:<port>`
- `http://192.168.x.x:<port>`

如果浏览器报 `Network Error`，而后端终端显示 `200 OK`，优先检查响应头是否包含：

```text
access-control-allow-origin: http://localhost:5173
```

## 7. 启动与验证

在 `location/backend` 目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

若使用已有 Conda 环境：

```powershell
conda activate elk
cd C:\Users\zhurunjie\Desktop\elk\location\backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

验证当前 import 的源码路径：

```powershell
python -c "import app.main, app.api.v1.system; print(app.main.__file__); print(app.api.v1.system.__file__)"
```

验证接口和 CORS：

```powershell
curl.exe -i -H "Origin: http://localhost:5173" http://localhost:8000/api/v1/health
curl.exe -i -H "Origin: http://localhost:5173" http://localhost:8000/api/v1/system/status
```

## 8. 常见排错

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| `/system/status` 只有 4 个基础字段 | 8000 上跑的是旧代码或错误工作目录 | 停掉旧进程，从 `location/backend` 重新启动 |
| 前端显示 `Network Error` | CORS 头缺失或后端未运行 | 检查 curl 响应头和 8000 进程 |
| Kafka 显示不可用 | Kafka 容器未启动或 9092 未映射 | 检查 `docker compose ps` 和 `localhost:9092` |
| ES cluster health 为 unknown 或 `error` 含 `missing authentication` | ES 启用安全认证但未配置账号密码 | 在 `location/backend/.env` 或 `location/.env` 中设置 `ELASTICSEARCH_USERNAME`、`ELASTICSEARCH_PASSWORD`（或沿用 `ELASTIC_PASSWORD`），重启后端 |
| Docker 容器状态 unknown | 后端进程无法访问 Docker CLI/Engine | 确认 Docker Desktop 运行，当前用户能执行 `docker ps` |

## 9. 开发约束

- API 层禁止直接写 Docker/Kafka/ES 复杂逻辑，只调用 service。
- 返回给前端的字段必须结构化且稳定，避免临时自然语言拼接。
- 每次修改模块代码后，同步维护对应 `app/**/DEV.md`。
- 不要删除 `/api/v1/system/status` 的 `docker`、`containers`、`services` 字段。
- 不要把容器启动、停止、删除等写操作加入系统状态接口。

## 10. 当前状态表

| 模块 | 当前状态 | 风险 | 说明 |
| --- | --- | --- | --- |
| App/CORS | 可用 | 低 | 支持本地前端跨域访问 |
| API 路由 | 可用但需完善 | 中 | health/system/logs/diagnosis 已挂载 |
| 系统状态 | 可用 | 中 | Docker/Kafka 可真实探测；ES health 在配置 `basic_auth` 后可穿透认证 |
| 全链路验证 | 可用 | 中 | 系统 API 可触发多线程 `verify_log_pipeline_full` 并返回节点状态与终端输出 |
| 日志查询 | 可用但需继续联调 | 中 | 已接入真实 ES search；依赖 ES 索引与数据 |
| 智能诊断 | 初步可用/持续扩展 | 中 | 规则优先并可拉取 ES 上下文，复杂链路后续接 LangGraph |
| 模拟日志 | 可用但需继续增强 | 中 | 已覆盖 Nginx Web Server 日志；模拟日志 `timestamp` 统一输出 UTC `Z` 时间；支持任务层多线程生产并统一写入 Kafka topic |

## 11. 开发日志

| 日期 | 修改内容 | 涉及文件 | 结果 | 遗留问题 |
| --- | --- | --- | --- | --- |
| 2026-05-14 | 建立后端目录级 DEV 文档 | `backend/DEV.md` | 汇总当前真实后端状态、接口契约、启动验证与排错方式 | 后续代码变更需持续维护 |
| 2026-05-14 | ES 客户端支持安全认证（与监控用 cluster health 共用） | `app/core/config.py`、`app/services/elasticsearch/client.py`、`app/tasks/verify_log_pipeline_full.py`、`.env.example` | `get_es_client()` 在配置密码后使用 `basic_auth`；配置支持 `ELASTIC_PASSWORD` 别名 | 密码需由运维本地注入，勿提交真实密钥 |
| 2026-05-18 | 完成 P0 修复：诊断接口字段对齐，日志查询接入真实 ES search | `app/schemas/diagnosis.py`、`app/services/diagnosis/*`、`app/services/elasticsearch/log_query_service.py`、`tests/test_health.py` | 健康检查、日志查询、诊断接口均可稳定返回；ES 未启动时日志查询返回可诊断错误结构 | `pytest` 未安装；真实 ES 命中需启动 ELK 后联调 |
| 2026-05-18 | 为系统状态页新增全链路验证 API | `app/api/v1/system.py`、`app/schemas/system.py`、`app/services/pipeline_verification.py` | 前端可展示“日志生产 -> Kafka -> Logstash -> ES”节点状态与终端输出 | 长耗时验证依赖 Kafka/Logstash/ES 在线 |
| 2026-05-19 | 新增 Nginx Web Server 日志生成与多线程 Kafka 生产 | `app/services/simulation/log_generator.py`、`app/tasks/run_log_producer.py`、`tests/test_health.py` | `build_mock_log()` 可产出 `web_server`；`--workers` 多线程统一写入 `app-logs` 已验证 | 后续可补指定日志类型与 TPS 控制 |
| 2026-05-19 | 全链路验证纳入多线程生成测试 | `app/tasks/verify_log_pipeline_full.py`、`app/services/pipeline_verification.py`、`app/schemas/system.py`、`app/api/v1/system.py` | 前端快速检测默认以 2 workers 验证多线程生成到 ES 命中 | 节点解析基于脚本输出关键阶段 |
| 2026-05-19 | 修复模拟日志时间戳时区问题 | `app/services/simulation/log_generator.py`、`app/services/simulation/DEV.md`、`backend/DEV.md` | 新生成日志的 `timestamp` 为 UTC ISO-8601 `Z` 格式，Nginx `time_local` 保留本地时区偏移，降低 Kibana 相对时间范围查询偏差 | 已写入 ES 的旧日志时间不会回填，需要重新生成新日志验证 |
