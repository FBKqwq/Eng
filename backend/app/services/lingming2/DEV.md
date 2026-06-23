# lingming2 模块开发记录

## 模块状态

| 功能 | 状态 | 说明 |
| --- | --- | --- |
| Schema 定义 | ✅ 已完成 | `app/schemas/goulingming.py` |
| API 路由 | ✅ 已完成 | `app/api/v1/goulingming.py` |
| 路由注册 | ✅ 已完成 | `app/api/router.py` 已注册 `/v1/goulingming` |
| 统计指标 ES 聚合 | ✅ 已完成（开关控制） | `USE_ES_STATS=False`；改为 True 启用 |
| 服务状态 Docker + ES | ✅ 已完成（开关控制） | `USE_DOCKER_ES_SERVICES=False`；改为 True 启用 |
| 日志检索后端端点 | ✅ 无需开发 | `POST /logs/search` 已支持 `log_types: ['application']` |

## 功能开关

```python
# app/services/lingming2/service.py
USE_ES_STATS = False           # 改为 True：统计指标从 ES aggregate_traffic + aggregate_errors 获取
USE_DOCKER_ES_SERVICES = False  # 改为 True：服务状态从 Docker + ES QPS 聚合获取
```

## 已实现功能

- [x] `POST /api/v1/goulingming/stats` - 核心统计指标（ES 或 mock）
- [x] `GET /api/v1/goulingming/services` - 服务节点状态（Docker + ES 或 mock）
- [x] API 层与 Service 层分层，无业务逻辑内联
- [x] 环比 delta 计算（上一等长时间窗口对比）
- [x] Docker 容器状态归一化（healthy/degraded/down/unknown）
- [x] 流量趋势折线图（TrafficTrendChart，mock）
- [x] 错误率趋势折线图（ErrorTrendChart，mock）
- [x] 延迟分布柱状图（LatencyChart，mock）
- [x] 图表随 timeRange 联动刷新

## 开发日志

### 2026-06-23 - 初始化（第一轮）

- 创建模块目录 `app/services/lingming2/`
- 备案 API 路由文件 `app/api/v1/goulingming.py`
- 备案 Schema 文件 `app/schemas/goulingming.py`

### 2026-06-23 - 重构（按 skill 规范）

- 新建 `app/services/lingming2/service.py`，业务逻辑全部下沉
- 新建 `app/api/v1/goulingming.py`，API 路由只做参数解析和调用 service
- 新建 `app/schemas/goulingming.py`，完整定义请求/响应模型

### 2026-06-23 - 真实数据接入

- `USE_ES_STATS` 接入 `aggregate_traffic` + `aggregate_errors` + `aggregate_latency`
- `USE_DOCKER_ES_SERVICES` 接入 `get_docker_status` + ES QPS 聚合
- 添加 `_parse_cpu` / `_ensure_tz` 等工具函数
- 日志检索确认无需改后端，`POST /logs/search` 已支持 `log_types: ['application']`

## 外部文件变更记录

### app/api/v1/goulingming.py

- **路由**：`POST /api/v1/goulingming/stats`、`GET /api/v1/goulingming/services`
- **用途**：Goulingming 统计面板数据入口，调用 `lingming2/service.py`
- **维护者**：本模块（lingming2）
- **最后变更**：2026-06-23 重构，移除内联业务逻辑

### app/schemas/goulingming.py

- **用途**：goulingming 域的请求/响应数据结构定义
- **包含模型**：`StatsQueryRequest`、`GoulingmingStatsData`、`GoulingmingServiceItem`、`GoulingmingServiceListData`
- **维护者**：本模块（lingming2）
- **最后变更**：2026-06-23 重构，完善字段定义与文档

### app/api/router.py

- **变更内容**：新增 `goulingming_router` 注册至 `/v1/goulingming`
- **维护者**：本模块（lingming2）
- **最后变更**：2026-06-23 初始化

## TODO（已完成全部）

- [x] 统计指标接入 ES 真实聚合（`USE_ES_STATS=True` 启用）
- [x] 服务状态接入 Docker 真实状态（`USE_DOCKER_ES_SERVICES=True` 启用）
- [x] 服务 QPS/错误率接入 ES 实时聚合（`_query_service_es_metrics`）
- [x] 日志检索后端端点（已确认无需开发，`POST /logs/search` 已支持）
- [x] 流量趋势折线图（前端 mock，真实数据后接 `/logs/aggregate`）
- [x] 错误率趋势折线图（前端 mock）
- [x] 延迟分布柱状图（前端 mock）
