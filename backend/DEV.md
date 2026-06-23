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
| LLM / Chain | langchain-openai（可选，无 Key 时规则降级） |
| 流程编排 | langgraph |
| 定时调度 | apscheduler |
| 测试/联调 | pytest、FastAPI TestClient、curl |

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
| `app/services/elasticsearch/` | ES client、日志查询、聚合、上下文、字段目录、索引模板、cluster health |
| `app/services/diagnosis/` | 声明式规则分流、`match_log`、同步诊断门面 |
| `app/services/langchain/` | LLM 管理、Prompt、证据压缩、report/diagnosis Chain（`relation_chain`/`alert_chain` 仍占位） |
| `app/services/analysis/` | LangGraph 定时子图、规则子图、scheduler、trigger_scanner（`graph_main` 仍占位，M6） |
| `app/services/tools/` | 10 个 LangChain StructuredTool + registry（`create_mcp_server` 仍占位，M7） |
| `app/services/report/` | `analysis-results-*` 报告持久化读写 |
| `app/services/alert/` | `alerts-*` 预警持久化、去重与确认状态机 |
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
| GET/POST | `/api/v1/logs/*` | 日志查询、`GET /fields` 字段目录、`POST /aggregate` 受控聚合 |
| POST | `/api/v1/diagnosis` | 智能诊断入口（规则分流 + ES 上下文） |
| GET | `/api/v1/reports/recent` | 最近分析报告（真实 ES，`report_service`） |
| GET | `/api/v1/reports/{id}` | 报告详情 |
| GET | `/api/v1/alerts/active` | 活跃预警列表（真实 ES，`alert_service`） |
| POST | `/api/v1/alerts/{id}/ack` | 预警确认（`active` → `acknowledged`） |

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

> **里程碑**：M1～M5 已于 2026-06-22 收口；本地 `pytest` 110 passed、3 skipped。下一阶段为 M6（主图收敛）/ M7（关系发现 + MCP）。

| 模块 | 当前状态 | 风险 | 说明 |
| --- | --- | --- | --- |
| App/CORS | 可用 | 低 | 支持本地前端跨域访问 |
| API 路由 | 可用但需完善 | 中 | health/system/logs/diagnosis/reports/alerts 均已挂载并对接 service |
| 系统状态 | 可用 | 低 | Docker/Kafka/ES 可真实探测；ES health 在配置 `basic_auth` 后可穿透认证 |
| 全链路验证 | 可用 | 中 | 系统 API 可触发多线程 `verify_log_pipeline_full` 并返回节点状态与终端输出 |
| 日志查询/聚合 | 可用 | 中 | M1 真实 ES search/aggregate/fields/context；依赖索引模板与数据 |
| 同步智能诊断 | 可用 | 中 | 关键词规则 + ES 上下文；声明式 `match_log` 供规则子图使用 |
| LangChain 层 | M3 已实现 | 低 | report/diagnosis Chain + 无 Key 规则降级；`relation_chain`/`alert_chain` 仍占位 |
| LangGraph 层 | M4/M5 子图已实现 | 中 | 定时六节点子图 + 规则七节点子图；`graph_main` 主图仍占位（M6） |
| MCP/工具层 | M2 已实现 | 低 | 10 StructuredTool + registry；`create_mcp_server` 仍占位（M7） |
| 报告持久化 | M4 已实现 | 中 | `analysis-results-*` 读写；scheduler 定时写入闭环 |
| 预警持久化 | M5 已实现 | 中 | `alerts-*` 读写 + 去重；trigger_scanner 扫描写入闭环 |
| 模拟日志 | 可用但需继续增强 | 中 | 7 大类日志；UTC `Z` 时间戳；多线程 Kafka 生产 |

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
| 2026-06-16 | 按总体规划完成后端框架占位更新 | 见 `doc/后端开发总体规划-Services-LangGraph-MCP.md` 全文对应目录 | ES 扩建四模块、langchain/analysis/tools/report/alert 分域占位、API/schema/config 扩展 | 后续 M1→M7 逐步实现 |
| 2026-06-22 | M1～M5 里程碑收口，同步目录级 DEV 文档 | `backend/DEV.md`、`app/api/DEV.md`、`app/services/DEV.md`、`app/tasks/DEV.md`、`app/schemas/DEV.md`、`doc/后端开发总体规划-Services-LangGraph-MCP.md` §0 | ES 聚合/上下文、工具层、LangChain、定时/规则子图、报告/预警持久化与 API 均已真实实现；pytest 110 passed | M6 `graph_main`、M7 MCP/关系发现待开发；频率规则聚合待 P1 |
| 2026-06-23 | **首次真实 ELK+Kafka 端到端联调，修复 3 处问题** | `app/services/elasticsearch/aggregation_service.py`、`app/services/analysis/schemas.py`、`graph_scheduled.py`、`graph_rule.py`、`graph_main.py` + 对应 DEV.md；基础设施 `POST /_license/start_basic` | ① 基础设施：ES trial 许可证过期致 security 不合规（cluster.health 403），已启用永久 basic 许可证恢复；② 聚合 bug：`_terms_field` 误加 `.keyword` 致 terms 聚合恒空，已修；③ 时区 bug：定时窗口用 naive 本地时间致 ES 查询偏移 8 小时、证据恒空，已改 UTC。修复后 produce→Kafka→Logstash→ES、查询/聚合/上下文、定时+规则主图（真实 qwen LLM）、报告/预警持久化与去重幂等全链路跑通 | `cluster_status.get_elasticsearch_health_snapshot` 仍在 cluster.health 失败时整体判 `available=False`（健壮性 P2，basic 许可证永久有效后不复现）；scheduler 默认 15min 窗口，一次性触发需保证数据新鲜 |
