# Frontend DEV 文档

## 1. 文档用途

本文档是 `location/frontend/` 目录级维护基线，用于说明 Vue 前端当前真实状态、路由约定、API 契约、系统状态页展示规则和本地开发验证方式。后续修改前端代码时，应同步更新本文档。

## 2. 前端定位

前端是 ELK + Kafka + LangGraph 电商日志分析项目的展示层，职责包括：

- 展示首页、日志监控、智能诊断、实验结果、系统状态页面。
- 通过后端 API 获取日志、诊断结果、系统状态。
- 不直接访问 Elasticsearch、Kafka、Docker 或 Kibana API。
- 为开发/排查提供 `/temp/developer` 手动入口，复用系统状态页。

## 3. 技术栈

| 类别 | 当前选型 |
| --- | --- |
| 框架 | Vue 3 |
| 构建工具 | Vite |
| 路由 | vue-router |
| HTTP | axios |
| 默认端口 | 5173 |

## 4. 目录职责

| 路径 | 职责 |
| --- | --- |
| `src/api/` | API wrapper，只封装后端请求 |
| `src/views/` | 页面级组件：home、monitor、diagnosis、results、system |
| `src/components/` | 可复用组件，如诊断卡片、服务状态卡 |
| `src/layout/` | 侧边栏与主内容布局 |
| `src/router/` | 路由定义 |
| `src/utils/` | 状态归一化、格式化等工具 |
| `src/assets/` | 样式和静态资产 |

## 5. 当前路由

| 路径 | 组件 | 入口 |
| --- | --- | --- |
| `/` | 首页 | 侧边栏 |
| `/monitor` | 日志监控 | 侧边栏 |
| `/diagnosis` | 智能诊断 | 侧边栏 |
| `/results` | 实验结果 | 侧边栏 |
| `/system` | 系统状态 | 侧边栏 |
| `/temp/developer` | 系统状态 | 手动访问，用于开发排查 |

注意：历史文档中出现过 `/state/*` 路由约定，当前源码已不使用该约定。不要再把导航恢复到 `/state/`。

## 6. API 契约

`.env.development` 当前配置：

```text
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_KIBANA_URL=http://localhost:5601
```

系统状态页会请求：

| 方法 | API wrapper | 实际路径 | 作用 |
| --- | --- | --- | --- |
| GET | `getApiHealth()` | `/api/v1/health` | 后端 API 探活 |
| GET | `getSystemStatus()` | `/api/v1/system/status` | 系统、Kafka、ES、Docker 容器状态 |
| POST | `verifyPipeline()` | `/api/v1/system/pipeline/verify` | 触发后端多线程全链路验证并返回节点状态与终端输出 |

`/api/v1/system/status` 需要包含：

- `kafka_bootstrap_servers`
- `kafka_topic`
- `elasticsearch_hosts`
- `elasticsearch_index_pattern`
- `kafka`
- `elasticsearch`
- `docker`
- `containers`
- `services`

## 7. 系统状态页展示规则

系统状态页位于 `src/views/system/index.vue`，复用 `src/components/system/ServiceStatusCard.vue` 与 `src/utils/systemStatus.js`。

展示内容：

- Frontend：当前页面加载状态。
- Backend：`/api/v1/system/status` 或 `/api/v1/health` 的浏览器可见状态。
- Kafka：broker/topic 快照与 Kafka 容器状态。
- Elasticsearch：cluster health 与 Elasticsearch 容器状态。
- Logstash：容器状态与端口。
- Kibana：容器状态与 Kibana URL。
- 配置快照：Kafka bootstrap servers、Kafka topic、ES hosts、ES index pattern。
- 全链路验证：通过“快速检测”触发后端多线程 `verify_log_pipeline_full`，展示“日志生产 -> Kafka 接收 -> Logstash 处理 -> Elasticsearch 检索”四个节点状态，并显示验证终端输出。

兜底规则：

- 优先使用后端返回的结构化字段。
- 若 `kafka` 或 `elasticsearch` 专项探测缺失，使用 `containers`、`services` 或 `docker.containers`。
- 若 Elasticsearch cluster health 返回 `unknown` 或 `available=false`，但 Docker 容器为 `running`，页面显示容器运行态，并保留 cluster health 错误详情。
- 禁止把系统状态页退回为“按钮 + raw JSON `<pre>`”调试页。

## 8. 本地启动与验证

安装依赖：

```powershell
cd C:\Users\zhurunjie\Desktop\elk\location\frontend
npm install
```

启动开发服务：

```powershell
npm.cmd run dev -- --host 0.0.0.0 --port 5173
```

构建验证：

```powershell
npm.cmd run build
```

浏览器验证：

- 平台入口：`http://localhost:5173/`
- 系统状态：`http://localhost:5173/system`
- 开发者状态：`http://localhost:5173/temp/developer`

系统状态页正常时应看到：

- `Backend API` 为正常。
- Kafka、Elasticsearch、Logstash、Kibana 服务卡均可展示容器状态。
- Kafka 详情展示 `localhost:9092`、`app-logs`、`kafka-1`。
- Elasticsearch 详情展示 `location-elasticsearch-1`、端口、CPU、内存等容器信息。

## 9. 常见排错

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| 页面出现 `Network Error` | 后端未启动或 CORS 头缺失 | 用 curl 检查 `access-control-allow-origin` |
| 只显示前后端正常，Kafka/ES unknown | 后端 `/system/status` 缺少 `containers/services/docker` | 检查 8000 是否启动了旧后端 |
| `/temp/developer` 空白 | 路由缺失或 Vite 未加载最新构建 | 检查 `src/router/index.js` 是否有 `/temp/developer` |
| Kafka topic 不存在 | Kafka 正常但 `app-logs` topic 未创建 | 后端会显示 `configured_topic.exists=false` |
| ES cluster health unknown | Elasticsearch 认证未配置 | 页面用容器 running 兜底，错误作为详情展示 |

## 10. 当前状态表

| 模块 | 当前状态 | 风险 | 说明 |
| --- | --- | --- | --- |
| 路由/Layout | 可用 | 低 | `/` 平台路由和 `/temp/developer` 手动入口可用 |
| API wrapper | 可用 | 低 | system.js 包含 health/status 查询与 pipeline verify |
| 系统状态页 | 可用 | 中 | 可展示 Kafka/ES/Docker 容器状态与全链路验证结果，ES health 依赖后端认证 |
| 日志监控页 | 占位/待增强 | 中 | 当前偏 Kibana 跳转，搜索列表能力待完善 |
| 智能诊断页 | 初步可用 | 中 | 表单与结果卡已有，依赖后端诊断能力 |
| 实验结果页 | 占位 | 中 | 后续展示性能测试和案例分析 |

## 11. 开发约束

- 页面不得直接使用 axios/fetch，应通过 `src/api/*.js`。
- 前端不得直接访问 ES、Kafka、Docker API。
- 系统状态页不能硬编码容器假数据，只能展示后端返回值。
- 路由变更必须同步更新本文档。
- 每次修改后至少运行 `npm.cmd run build`。

## 12. 开发日志

| 日期 | 修改内容 | 涉及文件 | 结果 | 遗留问题 |
| --- | --- | --- | --- | --- |
| 2026-05-14 | 重建前端目录级 DEV 文档 | `frontend/DEV.md` | 清理过期 `/state/` 约定，记录当前路由、API、系统状态展示规则 | 后续页面增强需持续维护 |
| 2026-05-14 | 恢复系统状态页和 `/temp/developer` | `src/views/system/index.vue`、`src/router/index.js`、`src/api/system.js`、`src/utils/systemStatus.js` | `/temp/developer` 可展示 Kafka、ES、Logstash、Kibana 容器状态 | ES cluster health 认证后续处理 |
| 2026-05-18 | 系统状态页新增全链路快速检测面板 | `src/views/system/index.vue`、`src/api/system.js` | 可触发后端 pipeline verify，展示四节点状态与 `verify_log_pipeline_full` 输出 | 长耗时验证依赖后端接口与 Kafka/ELK 当前运行状态 |
| 2026-05-19 | 快速检测纳入多线程日志生成验证 | `src/views/system/index.vue` | 默认传 `workers=2`，覆盖多线程日志生产到 ES 命中的链路 | 后续可把 workers 暴露为页面参数 |
