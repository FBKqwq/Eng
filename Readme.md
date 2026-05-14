# ELK + Kafka + LangGraph 电商日志分析与智能诊断系统

本项目是一个面向课程设计/工程实践的电商日志分析平台，使用 Kafka、Logstash、Elasticsearch、Kibana 构建日志链路，使用 FastAPI 提供后端 API，使用 Vue 3 + Vite 提供前端页面，并预留规则诊断与 LangGraph 智能诊断扩展能力。

## 1. 项目能力

- Kafka：日志消息缓冲与 topic 管理。
- Logstash：从 Kafka 消费日志并写入 Elasticsearch。
- Elasticsearch：日志存储、检索与聚合。
- Kibana：日志可视化入口。
- FastAPI 后端：健康检查、日志查询、系统状态、智能诊断 API。
- Vue 前端：首页、日志监控、智能诊断、实验结果、系统状态页面。
- 开发者系统状态页：展示 Backend、Kafka、Elasticsearch、Logstash、Kibana、Docker 容器运行状态。

## 2. 项目结构

```text
location/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── core/         # 配置
│   │   ├── schemas/      # Pydantic 数据契约
│   │   ├── services/     # Kafka/ES/Docker/诊断/模拟服务
│   │   └── tasks/        # 独立任务脚本
│   └── DEV.md            # 后端目录级维护文档
├── frontend/             # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── api/          # API wrapper
│   │   ├── views/        # 页面
│   │   ├── components/   # 组件
│   │   ├── layout/       # 布局
│   │   └── utils/        # 工具
│   └── DEV.md            # 前端目录级维护文档
├── elasticsearch/        # Elasticsearch 镜像与配置
├── logstash/             # Logstash 镜像与 pipeline
├── kibana/               # Kibana 镜像与配置
├── setup/                # Elastic 内置用户初始化
├── extensions/           # Beats 扩展配置
├── docker-compose.yml    # ELK + Kafka 基础设施编排
└── .env                  # Elastic Stack 环境变量
```

## 3. 服务端口

| 服务 | 地址 | 说明 |
| --- | --- | --- |
| 前端 | `http://localhost:5173` | Vue/Vite 开发服务 |
| 后端 | `http://localhost:8000` | FastAPI |
| 后端文档 | `http://localhost:8000/docs` | Swagger UI |
| Kafka（宿主机 Producer / 后端） | `localhost:9092` | `PLAINTEXT_EXTERNAL`，与 `KAFKA_ADVERTISED_LISTENERS` 中 `localhost` 一致 |
| Kafka（Compose 内，如 Logstash） | `kafka:29092` | `PLAINTEXT_INTERNAL`，容器间请用服务名 `kafka`，勿用 `localhost:9092` |
| Elasticsearch | `http://localhost:9200` | ES HTTP API |
| Kibana | `http://localhost:5601` | Kibana UI |
| Logstash API | `http://localhost:9600` | Logstash monitoring API |

## 4. 关键 API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/health` | 后端健康检查 |
| GET | `/api/v1/system/status` | 系统状态综合快照 |
| GET | `/api/v1/system/containers` | Docker 容器状态 |
| GET/POST | `/api/v1/logs/*` | 日志查询 |
| POST | `/api/v1/diagnosis` | 智能诊断 |

`/api/v1/system/status` 是前端系统状态页的核心接口，必须包含：

- `kafka`
- `elasticsearch`
- `docker`
- `containers`
- `services`

## 5. 从零开始部署教程

以下步骤以 Windows + PowerShell 为主，路径以当前项目目录 `C:\Users\zhurunjie\Desktop\elk\location` 为例。其他系统可按同等命令调整。

### 5.1 安装 Docker Desktop

1. 打开 Docker Desktop 官网下载安装包：
   - <https://www.docker.com/products/docker-desktop/>
2. 安装时建议勾选 WSL 2 backend。
3. 安装完成后重启电脑。
4. 启动 Docker Desktop，等待左下角或状态栏显示 Docker Engine 已运行。
5. 打开 PowerShell 验证：

```powershell
docker --version
docker compose version
docker ps
```

如果 `docker ps` 能正常返回表头，说明 Docker CLI 可用。

### 5.2 安装 Python

推荐 Python 3.10+。本项目当前在 Python 3.12 环境验证可用。

检查：

```powershell
python --version
```

如果使用 Conda：

```powershell
conda create -n elk python=3.12 -y
conda activate elk
```

### 5.3 安装 Node.js

推荐 Node.js 18+。

检查：

```powershell
node --version
npm --version
```

如果 PowerShell 执行 `npm` 报执行策略问题，可使用：

```powershell
npm.cmd --version
```

本项目命令中优先使用 `npm.cmd`。

### 5.4 获取项目并进入目录

```powershell
cd C:\Users\zhurunjie\Desktop\elk\location
```

确认目录下存在：

```powershell
dir
```

应能看到 `backend`、`frontend`、`docker-compose.yml`、`.env`。

### 5.5 检查 `.env`

根目录 `.env` 中至少需要：

```text
ELASTIC_VERSION=9.3.2
ELASTIC_PASSWORD='changeme'
LOGSTASH_INTERNAL_PASSWORD='changeme'
KIBANA_SYSTEM_PASSWORD='changeme'
```

课程/本地开发可继续使用 `changeme`；真实环境不要使用默认密码。

### 5.6 启动 ELK + Kafka 容器

首次启动建议先执行 setup：

```powershell
cd C:\Users\zhurunjie\Desktop\elk\location
docker compose --profile setup up setup
```

setup 完成后启动基础设施：

```powershell
docker compose up -d elasticsearch logstash kibana kafka
```

查看容器：

```powershell
docker compose ps
```

应看到：

- `kafka-1`
- `location-elasticsearch-1`
- `location-logstash-1`
- `location-kibana-1`

### 5.7 验证基础设施

Kafka 端口（宿主机对外映射仍为 9092）：

```powershell
netstat -ano | findstr :9092
```

**Kafka 双监听说明**：`docker-compose.yml` 中为单节点 Kafka 配置了 `PLAINTEXT_EXTERNAL`（`localhost:9092`，供本机后端与工具）与 `PLAINTEXT_INTERNAL`（`kafka:29092`，供同一 Compose 网络内的 Logstash 等容器）。修改后请重新拉起 Kafka 与 Logstash：

```powershell
docker compose up -d kafka logstash
```

**Logstash 消费 Kafka**：`logstash/pipeline/logstash.conf` 已增加 `kafka` input（环境变量 `LS_PIPELINE_KAFKA_BOOTSTRAP_SERVERS` 默认 `kafka:29092`，`LS_PIPELINE_KAFKA_TOPIC` 默认 `app-logs`），带 `pipeline_kafka_app_logs` 标签的事件写入索引 `app-logs-%{+YYYY.MM.dd}`；Beats/TCP 入口仍写入默认索引模式。

端到端冒烟（先发几条日志，再在 ES 中查索引）：

```powershell
cd C:\Users\zhurunjie\Desktop\elk\location\backend
python -m app.tasks.run_log_producer --count 5 --interval 0.2
```

一键全链路（生成 → Kafka → 脚本确认 Kafka → Logstash → ES 检索，需本机 Kafka、Logstash、ES 已运行；ES 密码可读 `location/.env` 的 `ELASTIC_PASSWORD`）：

```powershell
cd C:\Users\zhurunjie\Desktop\elk\location\backend
python -m app.tasks.verify_log_pipeline_full --count 2
```

等待数秒后（视 Logstash 消费延迟），使用已配置的 ES 账号查询（将 `elastic` 与密码换成你 `.env` 中的值）：

```powershell
curl.exe -s -u elastic:你的ES密码 -k "https://localhost:9200/_cat/indices/app-logs-*?v"
curl.exe -s -u elastic:你的ES密码 -k "https://localhost:9200/app-logs-*/_search?size=2&pretty"
```

若 `app-logs-*` 索引无法创建、Logstash 日志中出现 `logstash_internal` 对 `indices:admin/auto_create` 无权限，说明需刷新内置角色：已在本仓库 `setup/roles/logstash_writer.json` 中为 `app-logs-*` 增加与 `logstash-*` 相同的写索引权限。修改后请在 `location` 目录执行：

```powershell
docker compose --profile setup up setup
docker compose restart logstash
```

Elasticsearch：

```powershell
curl.exe http://localhost:9200
```

如果返回 `missing authentication credentials`，说明 ES 已启动且启用了安全认证，这是可接受的。

Kibana：

```powershell
curl.exe -I http://localhost:5601
```

也可以浏览器打开：

```text
http://localhost:5601
```

### 5.8 启动后端

```powershell
cd C:\Users\zhurunjie\Desktop\elk\location\backend
```

使用 venv：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

或使用 Conda：

```powershell
conda activate elk
cd C:\Users\zhurunjie\Desktop\elk\location\backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

重要：必须从 `location/backend` 目录启动，避免 import 到旧代码或错误路径。

确认 import 路径：

```powershell
python -c "import app.main, app.api.v1.system; print(app.main.__file__); print(app.api.v1.system.__file__)"
```

输出应指向：

```text
...\location\backend\app\main.py
...\location\backend\app\api\v1\system.py
```

### 5.9 验证后端

健康检查：

```powershell
curl.exe -i -H "Origin: http://localhost:5173" http://localhost:8000/api/v1/health
```

系统状态：

```powershell
curl.exe -i -H "Origin: http://localhost:5173" http://localhost:8000/api/v1/system/status
```

正确结果应包含响应头：

```text
access-control-allow-origin: http://localhost:5173
```

JSON 顶层应包含：

```text
kafka
elasticsearch
docker
containers
services
```

如果只看到 4 个字段：

```text
kafka_bootstrap_servers
kafka_topic
elasticsearch_hosts
elasticsearch_index_pattern
```

说明 8000 上运行的是旧后端或错误工作目录启动的后端。

### 5.10 启动前端

新开一个 PowerShell：

```powershell
cd C:\Users\zhurunjie\Desktop\elk\location\frontend
npm install
npm.cmd run dev -- --host 0.0.0.0 --port 5173
```

打开：

```text
http://localhost:5173/
```

系统状态页：

```text
http://localhost:5173/system
```

开发者状态页：

```text
http://localhost:5173/temp/developer
```

正常状态下应看到：

- Backend API 正常。
- Kafka 正常，显示 `localhost:9092`、`app-logs`、`kafka-1`。
- Elasticsearch 正常，显示 `location-elasticsearch-1`、端口、CPU、内存。
- Logstash 正常。
- Kibana 正常。

### 5.11 构建前端

```powershell
cd C:\Users\zhurunjie\Desktop\elk\location\frontend
npm.cmd run build
```

构建产物位于：

```text
frontend/dist/
```

## 6. 常见问题

### 6.1 前端显示 Network Error

检查后端 CORS：

```powershell
curl.exe -i -H "Origin: http://localhost:5173" http://localhost:8000/api/v1/system/status
```

如果没有 `access-control-allow-origin`，说明后端不是当前版本或 CORS 未生效。

### 6.2 8000 被旧进程占用

查端口：

```powershell
netstat -ano | findstr :8000
```

结束进程：

```powershell
Stop-Process -Id <PID> -Force
```

如果找不到 PID，优先关闭所有旧的 Python/Uvicorn 终端窗口，再重新检查。

### 6.3 系统状态只显示前后端正常

说明后端返回缺少容器状态字段。检查：

```powershell
curl.exe http://localhost:8000/api/v1/system/status
```

必须包含 `containers` 和 `services`。

### 6.4 Elasticsearch health 显示 unknown

如果错误类似：

```text
AuthenticationException(401, 'security_exception', 'missing authentication credentials')
```

说明 ES 运行正常但开启了认证。当前开发者页面会用 Docker 容器状态展示 Elasticsearch 正常运行，并保留认证错误作为诊断详情。

### 6.5 Docker 权限问题

如果后端返回 Docker unavailable，检查：

```powershell
docker ps
```

若提示权限或 Docker Engine 未运行，请启动 Docker Desktop，等待 Engine 就绪后重试。

## 7. 开发维护规则

- 修改后端前先看 `backend/DEV.md` 和目标模块 `app/**/DEV.md`。
- 修改前端前先看 `frontend/DEV.md`。
- 修改系统状态链路时，必须同时考虑：
  - 后端 `/api/v1/system/status` 响应字段。
  - 前端 `src/api/system.js`。
  - 前端 `src/views/system/index.vue`。
  - 前端 `src/utils/systemStatus.js`。
- 不要把系统状态页退回 raw JSON 调试页。
- 不要删除 `/temp/developer` 手动排查入口。
- 不要在前端直接访问 Elasticsearch、Kafka 或 Docker。

## 8. 验证清单

后端：

```powershell
cd C:\Users\zhurunjie\Desktop\elk\location\backend
python -m compileall app
curl.exe -i -H "Origin: http://localhost:5173" http://localhost:8000/api/v1/system/status
```

前端：

```powershell
cd C:\Users\zhurunjie\Desktop\elk\location\frontend
npm.cmd run build
```

浏览器：

```text
http://localhost:5173/temp/developer
```

应确认：

- 无 `Network Error`。
- 正常服务数量包含 Frontend、Backend、Kafka、Elasticsearch、Logstash、Kibana。
- Kafka 和 Elasticsearch 卡片显示容器详情。

## 9. 相关文档

- [后端维护文档](./backend/DEV.md)
- [前端维护文档](./frontend/DEV.md)
- [后端启动说明](./backend/README.md)
- [前端启动说明](./frontend/README.md)
