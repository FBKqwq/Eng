# Schemas 模块 DEV 文档

## 1. 文档用途说明
本文档用于维护 `app/schemas/` 的数据契约开发状态，确保前后端字段一致、请求响应结构稳定、避免重复定义与随意改字段。

## 2. 项目模块总览
| 文件 | 主要职责 |
|---|---|
| `app/schemas/log.py` | 日志查询相关请求与响应结构 |
| `app/schemas/diagnosis.py` | 诊断请求与诊断结果结构 |
| `app/schemas/report.py` | 分析报告列表与详情契约（API 已对接 `report_service`） |
| `app/schemas/alert.py` | 预警列表与确认契约（API 已对接 `alert_service`） |

## 3. 模块职责边界
- 应该放在这里：Pydantic 模型、字段约束、接口契约定义。
- 不应该放在这里：路由逻辑、ES 查询逻辑、诊断业务流程。

## 4. 已实现功能清单
- 已存在日志与诊断两类 schema 文件。
- 已形成基础请求/响应契约载体。
- `DiagnosisRequest` 已补充 `keyword` 字段，兼容诊断页自由输入与规则分流。
- `PipelineVerifyRequest/Response` 已定义，用于系统状态页展示多线程全链路验证节点与终端输出。
- `WebServerLog` 已按 Nginx access/error log 常见字段补齐，纳入 `LogType.web_server` 与 `AnyLog`。
- `schemas/report.py`、`schemas/alert.py`：列表/详情/确认响应模型已建立，并由 M4/M5 API 真实消费。

## 5. 待开发功能清单（P0-P3）
- P0：统一通用响应结构与错误结构。
- P1：补齐 metrics/system 相关 schema。
- P2：细化字段校验规则、示例值与说明。
- P3：补充版本化契约兼容策略。

## 6. 模块状态表
| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| Schemas | M1/M4/M5 契约已对齐 API | 2026-06-22 | elk-backend-agent | 低 | report/alert 已由占位转为真实对接 |

## 7. 禁止重复实现清单
| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| 请求响应字段定义 | `app/schemas/` | 禁止在 `api/` 或 `services/` 内临时拼裸 dict 充当契约 |
| 字段合法性校验 | `app/schemas/` | 禁止把参数合法性散落在多个 route 函数里 |

## 8. 真实实现与设计愿景差异
| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 统一数据契约 | 所有接口均有清晰 schema 与错误结构 | 目前仅覆盖部分领域 | 逐步补齐并收敛到统一基类 |

## 9. 开发日志区
| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-05-06 | 初始化 Schemas 模块 DEV 文档 | `app/schemas/DEV.md` | 建立契约维护规范 | 待后续随功能更新同步维护 |
| 2026-05-18 | 补齐诊断关键词字段 | `app/schemas/diagnosis.py` | `DiagnosisRequest` 与诊断服务规则输入对齐，接口不再因缺失字段崩溃 | 后续需继续统一响应模型 |
| 2026-05-18 | 新增全链路验证响应契约 | `app/schemas/system.py` | 系统状态页可读取 `success`、`nodes`、`stdout/stderr` 展示验证结果 | 后续可抽出统一任务执行响应基类 |
| 2026-05-19 | 全链路验证请求支持 workers | `app/schemas/system.py` | `PipelineVerifyRequest.workers` 可控制验证脚本并发生成与发送线程数 | 当前限制 1~8 个 worker |
| 2026-05-19 | 补齐 Nginx Web Server 日志契约 | `app/schemas/log.py` | 新增 `LogType.web_server`、`WebServerLog`、Nginx log kind / upstream cache / scheme 等枚举，Pydantic 实例化验证通过 | 后续需在 simulation 生成器中实际产出该类日志 |
| 2026-06-16 | 新增 report/alert schema | `schemas/report.py`、`schemas/alert.py` | 列表/详情/确认响应模型就位 | 已由 M4/M5 API 对接 |
| 2026-06-22 | 同步 Schemas DEV 至 M5 现状 | `app/schemas/DEV.md` | report/alert 去占位标注；状态表更新 | P0 统一响应基类仍待办 |

## 2026-05-13 补充：System / Docker 状态响应 Schema

### 变更记录

| 日期 | 变更 | 涉及文件 | 说明 | 状态 |
| --- | --- | --- | --- | --- |
| 2026-05-13 | 新增系统 / Docker 状态响应 schema | `app/schemas/system.py` | 定义 `ContainerStatus`、`DockerStatusResponse`、`SystemStatusResponse`，支撑开发者监控页读取容器状态和配置快照 | 已验证 |

### Schema 职责

`app/schemas/system.py` 负责系统状态类 API 的响应结构。

| Schema | 用途 |
| --- | --- |
| `ContainerStatus` | 单个容器状态，包含归一化 `status`、Docker 原始状态、镜像、端口、CPU、内存、网络、IO、PIDs 等字段 |
| `DockerStatusResponse` | Docker 查询整体结果，包含 project、available、error 与 containers 映射 |
| `SystemStatusResponse` | `/system/status` 综合响应，包含 Kafka/Elasticsearch 配置快照、Docker 状态、containers/services 映射 |

状态值仅允许前端按以下语义处理：`running`、`down`、`unknown`。原始 Docker 文本保存在 `raw_state`、`raw_status`、`detail` 中，供开发者排查使用。

## 2026-05-13 补充：Kafka / Elasticsearch 配置快照 Schema

### 模块状态表更新

| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
| --- | --- | --- | --- | --- | --- |
| Schemas | 可用但需完善 | 2026-05-13 | codex | 中 | `SystemStatusResponse` 已补充 Kafka 与 Elasticsearch 运行快照契约 |

### 已实现功能清单更新

- `ElasticsearchHealthSnapshot`：展示 ES hosts、index pattern、cluster status（green/yellow/red/unknown）、节点数、分片数、文档数和错误信息。
- `KafkaStatusSnapshot`：展示 Kafka bootstrap servers、topic、broker/topic 数量、配置 topic 是否存在、分区数和副本数。

### 开发日志区

| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
| --- | --- | --- | --- | --- |
| 2026-05-13 | 补齐系统状态响应契约 | `app/schemas/system.py` | 前端可直接读取 `elasticsearch.cluster_status` 渲染红/黄/绿状态，也可读取 Kafka topic 快照 | 字段含义需在前端展示层继续映射颜色与提示文案 |
