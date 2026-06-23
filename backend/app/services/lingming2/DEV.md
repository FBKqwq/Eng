# lingming2 模块开发记录

## 模块状态

| 功能 | 状态 | 说明 |
| --- | --- | --- |
| 核心统计指标（stats） | 已备案（业务逻辑待下沉） | API 已实现，业务逻辑暂内联在路由文件中 |
| 服务节点状态（services） | 已备案（mock） | 数据暂用 mock，后续接 Docker 状态 |
| Schema 定义 | 已备案 | 放置在 `app/schemas/goulingming.py` |

## 已实现/待开发功能

- [x] `POST /api/v1/goulingming/stats` - 核心统计指标查询
- [x] `GET /api/v1/goulingming/services` - 服务节点状态列表
- [ ] 业务逻辑下沉至 `app/services/lingming2/` service 层
- [ ] 服务状态从 Docker 真实状态聚合
- [ ] 统计指标从 Elasticsearch 真实聚合查询

## 开发日志

### 2026-06-23 - 初始化

- 创建模块目录 `app/services/lingming2/`
- 备案 API 路由文件 `app/api/v1/goulingming.py`
- 备案 Schema 文件 `app/schemas/goulingming.py`

## 外部文件变更记录

### app/api/v1/goulingming.py

- **路由**：`POST /api/v1/goulingming/stats`、`GET /api/v1/goulingming/services`
- **用途**：Goulingming 统计面板数据入口，调用 lingming2 service 层（当前业务逻辑暂内联）
- **维护者**：本模块（lingming2）
- **最后变更**：2026-06-23 初始化，统计业务逻辑暂内联待下沉

### app/schemas/goulingming.py

- **用途**：goulingming 域的请求/响应数据结构定义
- **包含模型**：`GoulingmingStatsData`、`GoulingmingServiceItem`、`GoulingmingServiceListData`、`StatsQueryRequest`
- **维护者**：本模块（lingming2）
- **最后变更**：2026-06-23 初始化

### app/api/router.py

- **变更内容**：新增 `goulingming_router` 注册至 `/v1/goulingming`
- **维护者**：本模块（lingming2）
- **最后变更**：2026-06-23 初始化
