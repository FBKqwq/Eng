# Engineering Lab Platform

基于 Elastic Stack 的工程实验平台，集成日志、指标、健康检查等功能。

## 项目结构

- `backend/` - 基于 FastAPI 的后端服务
- `frontend/` - 基于 Vue 3 + Vite 的前端应用
- `extensions/` - Elastic Stack 扩展模块
  - `filebeat/` - 日志收集
  - `heartbeat/` - 服务可用性检测
  - `metricbeat/` - 系统指标采集

## 快速开始

### 前置要求

- Docker & Docker Compose
- Python 3.8+
- Node.js 16+

### 启动完整堆栈

```bash
# 启动基础 Elastic Stack
docker compose up

# 或包含特定扩展
docker compose -f docker-compose.yml -f extensions/filebeat/filebeat-compose.yml up
```

## How to re-execute the setup

如果您需要重新执行初始化设置（例���重新创建用户或重新初始化系统状态），可以按照以下步骤操作：

### 通过 Docker Compose 重新执行设置

```bash
# 停止并删除现有容器
docker compose down

# 重新启动，设置容器会自动执行初始化
docker compose up
```

### 手动执行设置容器

```bash
# 运行设置容器
docker compose run --rm setup
```

### 重新初始化特定用户

如果只需要重新初始化某些内置用户（如 `metricbeat_internal`、`heartbeat_internal`、`filebeat_internal`、`beats_system` 等），可以：

1. 连接到 Elasticsearch 容器
2. 执行相应的用户管理命令

更多详情请参考各扩展模块的文档：
- [Filebeat 配置](./extensions/filebeat/README.md)
- [Heartbeat 配置](./extensions/heartbeat/README.md)
- [Metricbeat 配置](./extensions/metricbeat/README.md)

## 文档

- [Backend](./backend/README.md)
- [Frontend](./frontend/README.md)
- [Extensions](./extensions/README.md)
