# 后端开发总体规划：Services 模块、LangGraph 编排与 MCP 工具

> 项目名称：基于 ELK、Kafka 与 LangGraph 的模拟电商实时日志分析与智能异常诊断系统
> 文档定位：后端下一阶段开发的总体规划文档，覆盖三个核心问题：
>
> 1. `services/` 全模块开发规划（含 ES 聚合查询与 80+ 日志类型的使用设计）
> 2. LangChain 与 LangGraph 开发规划（一主图 + 两子图、Agent 中间层与工具需求）
> 3. 哪些 services 需要按 MCP 协议封装为 Agent 可调用工具
>
> 本文档与 `doc/LangChain技术目标.md`、`doc/LangGraph技术目标.md` 互为补充：技术目标文档回答"做成什么样"，本文档回答"按什么顺序、在哪些文件、以什么边界做出来"。
> 落地开发时仍以各模块 `DEV.md` 为唯一执行基线，若有冲突以模块 DEV.md 为准并记录差异。

---

## 0. 当前现状基线（截至 2026-06-22，M5 收口后）

> 本节为滚动现状快照；详细验收见各模块 `DEV.md` 与 `job/task_m*/STATUS.md`。§1 及以下章节仍为分阶段规划参考，落地以模块 DEV.md 为准。

| 模块 | 当前状态 | 风险 |
| --- | --- | --- |
| `services/simulation/` | 7 大类结构化日志可生成（audit 契约已定义） | 低 |
| `services/kafka/` | Producer、topic 预建、broker 探测可用 | 低 |
| `services/elasticsearch/` | client、search、聚合、上下文、字段目录、索引模板、cluster health（**M1 已完成**） | 低 |
| `services/diagnosis/` | 声明式规则 10 条 + `match_log` + 同步诊断门面（**M5**）；频率规则聚合待 P1 | 中 |
| `services/docker_status.py` / `pipeline_verification.py` | 只读探测与全链路验证可用 | 低 |
| `services/langchain/` | report/diagnosis Chain + 降级（**M3**）；`relation_chain`/`alert_chain` 占位 | 低 |
| `services/analysis/` | 定时子图 + 规则子图 + scheduler + trigger_scanner（**M4/M5**）；`graph_main` 占位（M6） | 中 |
| `services/tools/` | 10 StructuredTool + registry（**M2**）；`create_mcp_server` 占位（M7） | 低 |
| `services/report/` / `services/alert/` | `analysis-results-*` / `alerts-*` 真实读写（**M4/M5**） | 中 |
| `schemas/log.py` | 7 大类日志 + 查询/聚合/上下文契约 | 低 |
| API 层 | health/system/logs/diagnosis/reports/alerts 均已对接 service | 低 |

**结论**：数据底座与智能分析主链路（M1～M5）已成型；下一阶段主战场为 **M6 主图收敛**、**M7 关系发现 + MCP Server**、以及频率规则聚合与前端 `node_trace` 对接。

---

## 1. Services 全模块开发规划

### 1.1 目标目录全景

```text
backend/app/services/
├── elasticsearch/            # ES 访问域（扩建）
│   ├── client.py             # 已有：客户端单例
│   ├── log_query_service.py  # 已有：bool 查询 + 分页
│   ├── cluster_status.py     # 已有：健康快照
│   ├── field_catalog.py      # 新增：80+ 日志类型字段目录（核心）
│   ├── aggregation_service.py# 新增：受控聚合查询
│   ├── context_service.py    # 新增：trace/服务窗口/同类错误上下文
│   └── index_service.py      # 新增：索引模板与生命周期管理
├── kafka/                    # 已有，维持现状
├── simulation/               # 已有，按其 DEV.md P1 继续增强（trace 链路化）
├── diagnosis/                # 改造：规则引擎配置化，analyzer 收敛为门面
│   ├── rule_engine.py        # 改造：硬编码关键词 -> 可配置规则表
│   ├── rule_definitions.py   # 新增：规则声明（阈值/错误码/频率规则）
│   └── analyzer.py           # 改造：同步诊断门面，复杂任务转交 analysis 层
├── langchain/                # 新增：模型调用能力层（见第 2 章）
├── analysis/                 # 新增：LangGraph 编排层（见第 2 章）
├── tools/                    # 新增：MCP/Agent 工具层（见第 3 章）
├── report/                   # 新增：分析报告持久化域
│   └── report_service.py     # 写入/查询 analysis-results-*
├── alert/                    # 新增：预警持久化域
│   ├── alert_service.py      # 写入/查询 alerts-*
│   └── dedup.py              # 预警去重与幂等
├── docker_status.py          # 已有
└── pipeline_verification.py  # 已有
```

分域原则：**ES 访问、模型调用、流程编排、工具暴露、结果持久化五个域物理隔离**，任何一个域不得直接绕过另一个域访问其底层资源（例如 analysis 层不得直接拼 ES DSL，必须走 tools 或 elasticsearch 域）。

### 1.2 核心问题：80+ 日志类型如何设计使用

当前 `schemas/log.py` 定义了 7 大类日志（behavior / application / web_server / performance / security / infrastructure / audit），每类下又有 action、event_type、metric、component 等枚举细分，合计 80+ 种细分日志类型，且各类专有字段差异很大（如 web_server 有 30+ 个 Nginx 字段，behavior 有 tracking 漏斗字段）。这带来两个工程问题：

1. **索引问题**：所有类型混在一个索引里，mapping 字段爆炸、稀疏字段多、聚合性能差；
2. **聚合问题**：不同类型可聚合的维度和指标完全不同，不能用一个万能聚合接口对付所有类型。

#### 1.2.1 索引策略：一套公共模板 + 按 log_type 拆分索引

推荐采用 ES Composable Template 方案：

```text
component template: logs-common        # LogBase 公共字段（timestamp/log_id/log_level/log_type/
                                       # event_type/service_name/trace_id/user_id/status/...）
component template: logs-behavior      # behavior 专有字段（action/product_id/keyword/tracking.*）
component template: logs-application   # application 专有字段（request_path/status_code/error_code/db_*/redis_*）
component template: logs-web-server    # Nginx 字段（request_time/upstream_*/http_user_agent/...）
component template: logs-performance   # 指标字段（metric_name/metric_value/p95_ms/cpu_percent/...）
component template: logs-security      # 安全字段（risk_level/rule_id/ip_access_count/...）
component template: logs-infrastructure# 组件字段（component/resource_type/lag/es_cluster_health/...）
component template: logs-audit         # 审计字段（operator_id/before_value/after_value/...）

index template: app-logs-behavior-*        = logs-common + logs-behavior
index template: app-logs-application-*     = logs-common + logs-application
index template: app-logs-web-server-*      = logs-common + logs-web-server
...（共 7 个 index template）
```

索引命名：`app-logs-{log_type}-{yyyy.MM.dd}`，查询全量时用 `app-logs-*`，查询单类时用 `app-logs-application-*`。

落地方式：

- Logstash pipeline 按消息中的 `log_type` 字段路由到对应索引（基础设施依赖，后端先在 `index_service.py` 中提供模板创建能力，链路接通需基础设施配合修改 logstash output）；
- `index_service.py` 负责：创建 component/index template、校验 mapping 与 `schemas/log.py` 一致、提供 `init_indices` task 调用入口；
- 字段类型约定：所有枚举字段（log_level/event_type/service_name/error_code 等）映射为 `keyword`；耗时与指标映射为数值类型；`message` 为 `text` + `keyword` 子字段。

#### 1.2.2 字段目录（Field Catalog）：聚合查询的安全边界

这是 80+ 日志类型设计的核心抓手。新增 `elasticsearch/field_catalog.py`，以声明式注册每个 log_type 的可用字段能力：

```python
FIELD_CATALOG = {
    "application": {
        "filter_fields":   ["service_name", "event_type", "error_code", "status_code",
                            "request_path", "http_method", "downstream_service"],
        "terms_fields":    ["service_name", "error_code", "request_path", "event_type",
                            "exception_type", "downstream_service"],
        "metric_fields":   ["response_time_ms", "db_duration_ms", "retry_count"],
        "trace_capable":   True,
        "user_capable":    True,
    },
    "behavior": {
        "filter_fields":   ["action", "page", "product_id", "keyword", "conversion_step"],
        "terms_fields":    ["action", "page", "product_id", "keyword",
                            "tracking.conversion_step"],
        "metric_fields":   ["tracking.dwell_time_ms", "tracking.click_count",
                            "tracking.page_view_count"],
        "funnel_steps":    ["page_view", "product_click", "add_to_cart",
                            "checkout_click", "pay_button_click"],
        ...
    },
    "web_server": {
        "terms_fields":    ["request_uri", "status_code", "upstream_addr",
                            "http_user_agent", "upstream_cache_status"],
        "metric_fields":   ["request_time", "upstream_response_time",
                            "body_bytes_sent"],
        ...
    },
    # performance / security / infrastructure / audit 同理
}
```

字段目录的三个消费方：


| 消费方                      | 用途                                                                                     |
| ------------------------ | -------------------------------------------------------------------------------------- |
| `aggregation_service.py` | 校验聚合请求合法性：维度必须在 `terms_fields`，指标必须在 `metric_fields`，否则直接拒绝，避免对 text 字段做 terms 聚合打挂 ES |
| MCP 工具层                  | 工具的 schema 描述中暴露每类日志可查什么，LLM 只能在目录范围内选维度，**杜绝模型自由生成 DSL**                              |
| 前端日志筛选器                  | `GET /api/v1/logs/fields?log_type=xxx` 返回该类型可筛选字段，前端动态渲染筛选项                            |


#### 1.2.3 聚合查询服务设计

`aggregation_service.py` 不接受裸 DSL，只接受结构化参数（已有 `LogAggregateRequest` 契约），内部组装 DSL：

```text
入参：log_type(可选) + group_by + interval(可选) + metric(可选) + filters + top_n + 时间窗口
出参：LogAggregateResponse（buckets 列表，已有契约）
```

预置六类聚合模板（函数级封装，供 API 与 MCP 工具复用）：


| 模板                               | 面向日志类型                                 | 典型输出                                                       |
| -------------------------------- | -------------------------------------- | ---------------------------------------------------------- |
| `aggregate_traffic` 流量统计         | application + web_server               | 请求总量、按 interval 的时间直方图、请求高峰段                               |
| `aggregate_errors` 错误统计          | application + web_server               | 错误率、error_code 分布、status_code 分布、Top N 错误服务                |
| `aggregate_latency` 耗时统计         | application + web_server + performance | avg/p50/p95/p99 耗时、Top N 慢接口（percentiles + terms 嵌套聚合）     |
| `aggregate_behavior_funnel` 行为漏斗 | behavior                               | page_view → click → add_to_cart → checkout → pay 各步骤数量与转化率 |
| `aggregate_security` 安全统计        | security                               | risk_level 分布、被拦截次数、Top N 风险 IP/规则                         |
| `aggregate_infra_health` 基础设施    | infrastructure + performance           | 各组件健康比率、资源使用趋势、Kafka lag                                   |


关键实现要点：

1. 全部聚合走 `size: 0`，不回拉原始文档；
2. terms 聚合统一加 `top_n` 上限（默认 10，硬上限 50）；
3. 时间直方图统一用 `date_histogram` + `fixed_interval`（复用 `TimeInterval` 枚举）；
4. 多类型联合统计（如流量统计同时覆盖 application 与 web_server）通过查 `app-logs-application-*,app-logs-web-server-*` 多索引实现，不在内存中合并两次查询；
5. ES 不可用时返回稳定错误结构（沿用 `log_query_service.py` 的错误约定）。

#### 1.2.4 上下文查询服务设计

`context_service.py` 收编现有 `search_recent_context()` 并扩展为四个受控入口，直接服务于诊断子图：


| 函数                                         | 输入       | 行为                                    |
| ------------------------------------------ | -------- | ------------------------------------- |
| `get_trace_context(trace_id)`              | trace_id | 跨全部索引查同 trace 日志，按 timestamp 排序，还原调用链 |
| `get_service_window(service, start, end)`  | 服务名 + 窗口 | 查该服务窗口内日志，ERROR/WARN 优先返回，附带级别分布      |
| `get_similar_errors(error_code, window)`   | 错误码 + 窗口 | 查同类错误出现次数、涉及服务、时间分布（判断"集中爆发"）         |
| `get_user_recent_actions(user_id, window)` | 用户 + 窗口  | 查 behavior + application 中该用户行为序列     |


### 1.3 其余 services 模块规划

#### diagnosis 域改造

- `rule_engine.py`：从关键词 if/else 升级为读取 `rule_definitions.py` 的声明式规则表。规则三类：
  - 阈值规则：`status_code >= 500`、`response_time_ms > 3000`、`request_time > 3`；
  - 错误码规则：`PAY_FAIL`、`DB_TIMEOUT`、`CIRCUIT_OPEN`、`UNAVAILABLE`；
  - 频率规则：同服务 N 分钟内 ERROR ≥ M 条、同 IP 高频访问、同 user 连续失败（依赖 `aggregation_service` 计数）。
- 每条规则输出统一结构：`rule_id / rule_name / matched / severity / trigger_subgraph(bool)`，其中 `trigger_subgraph=True` 的规则将触发 LangGraph 规则子图。
- `analyzer.py` 保持为同步诊断门面：简单规则命中直接返回结构化结果（不进 LLM）；复杂诊断转交 `analysis/` 层的图执行入口。

#### report 域（新增）

- `report_service.py`：写入与查询 `analysis-results-*` 索引；
- 提供 `write_report(report)`、`list_recent_reports(limit, report_type)`、`get_report(report_id)`；
- 对前端暴露 `GET /api/v1/reports/recent`、`GET /api/v1/reports/{id}`（新增 `api/v1/reports.py` 与 `schemas/report.py`）。

#### alert 域（新增）

- `alert_service.py`：写入与查询 `alerts-*` 索引，状态机 `active → acknowledged → resolved`；
- `dedup.py`：幂等键 = `alert_type + affected_service + 时间桶(如 10 分钟)`，写入前查重，重复则只累加 `evidence_count` 并刷新时间；
- 对前端暴露 `GET /api/v1/alerts/active`、`POST /api/v1/alerts/{id}/ack`（新增 `api/v1/alerts.py` 与 `schemas/alert.py`）。

#### simulation 域（按现有 DEV.md 推进，仅列优先级）

- P1：同一 `trace_id` 生成网关 → 订单 → 库存 → 支付的多条连续链路日志（这是"隐藏关系发现"分析有效的前提，没有链路化数据，关系分析无米下锅）；
- P1：可配置异常比例、热点商品、高峰时段，便于制造"请求高峰后支付失败上升"这类可被图分析发现的模式。

### 1.4 Services 开发优先级总表


| 优先级 | 任务                                    | 所在模块          | 说明                          |
| --- | ------------------------------------- | ------------- | --------------------------- |
| P0  | `field_catalog.py` 字段目录               | elasticsearch | 聚合、工具、前端筛选三方的共同地基           |
| P0  | `aggregation_service.py` 六类聚合模板       | elasticsearch | LangGraph 定时子图的数据来源，不做则子图不通 |
| P0  | `index_service.py` + 按 log_type 拆索引模板 | elasticsearch | 决定后续所有聚合的性能与正确性             |
| P0  | `context_service.py` 四个上下文入口          | elasticsearch | 规则子图的数据来源                   |
| P1  | rule_engine 配置化 + 触发标记                | diagnosis     | 规则子图的触发源                    |
| P1  | report / alert 持久化域                   | report、alert  | 分析结果落地与前端展示的前提              |
| P1  | simulation trace 链路化                  | simulation    | 关系分析的数据前提                   |
| P2  | reports / alerts API 与 schema         | api、schemas   | 前端结果页对接                     |
| P2  | `GET /logs/fields` 字段目录接口             | api           | 前端动态筛选器                     |
| P3  | 聚合缓存、慢查询保护                            | elasticsearch | 演示稳定性增强                     |


---

## 2. LangChain 与 LangGraph 开发规划（重点）

### 2.1 总体架构与分工铁律

```text
Rule Engine（前置决策层）：确定性异常直接判断，决定是否触发图
LangGraph（流程编排层）：主图路由调度，子图执行查询与分析流程
LangChain（模型调用层）：Prompt、模型管理、结构化输出、证据压缩
Tools/MCP（外部能力层）：受控访问 ES、写报告、写预警、查系统状态
```

目录落点：

```text
backend/app/services/analysis/        # LangGraph 编排层
├── __init__.py
├── state.py            # 统一 Graph State
├── schemas.py          # 触发事件 / 报告 / 预警的内部模型
├── graph_main.py       # 主图
├── graph_scheduled.py  # 定时任务子图
├── graph_rule.py       # 规则任务子图
├── scheduler.py        # 定时触发入口（APScheduler / asyncio task）
└── trigger_scanner.py  # 扫描 ES 中命中规则的日志并触发规则子图

backend/app/services/langchain/       # LangChain 能力层
├── __init__.py
├── llm_manager.py      # 模型管理（API Key / 多模型 / 参数 / 重试）
├── prompts.py          # 集中 Prompt 模板
├── output_parsers.py   # Pydantic 结构化输出与校验重试
├── evidence_builder.py # 证据包压缩构建
├── report_chain.py     # 周期报告 Chain
├── diagnosis_chain.py  # 事件根因诊断 Chain
├── relation_chain.py   # 隐藏关系发现 Chain
└── alert_chain.py      # 预警解释 Chain
```

### 2.2 统一 Graph State

`analysis/state.py`，主图与两个子图共用一个 State（TypedDict / Pydantic）：

```python
class AnalysisState(TypedDict, total=False):
    # 触发上下文
    trigger_type: str            # "scheduled" | "rule"
    trigger_event: dict          # 规则触发时的原始日志事件
    time_window: dict            # {"start": ..., "end": ...}
    task_id: str                 # 本次图运行唯一 ID（幂等与追踪）

    # 查询与证据
    query_plan: dict             # ES Query Planner 产出的查询计划
    metrics: dict                # 聚合统计结果（代码算，不交给 LLM）
    raw_logs: list               # 原始样本日志（受 limit 控制）
    evidence_package: dict       # Evidence Builder 压缩后的证据包

    # 分析结果
    relations: list              # 关系发现结果
    analysis_report: dict        # 周期报告或事件诊断报告
    alert_candidate: dict        # 候选预警
    alert_decision: dict         # 最终预警判断（含去重结果）

    # 运行管理
    persist_result: dict         # 写入结果（报告 ID / 预警 ID）
    node_trace: list             # 各节点执行记录（耗时/状态），用于前端展示图运行过程
    errors: list                 # 节点级错误，不中断整图
```

设计要点：

1. `node_trace` 是答辩展示的关键——前端可以渲染"图执行了哪些节点、每个节点耗时多少、产出了什么"；
2. 任一节点失败写入 `errors` 并继续走降级路径（如 LLM 调用失败时报告退化为纯统计报告），整图不崩溃；
3. `task_id` 贯穿日志、报告、预警，保证可追溯。

### 2.3 主图（graph_main.py）

主图只做路由与收敛，不做任何具体分析。

```text
入口 normalize_trigger
  -> build_state
  -> route（条件边：trigger_type）
       ├── scheduled -> 定时任务子图（作为 subgraph 节点挂载）
       └── rule      -> 规则任务子图（作为 subgraph 节点挂载）
  -> merge_result
  -> alert_decision
  -> persist_result
  -> END
```


| 节点                  | 职责                                                               | 依赖的中间层/工具                                     |
| ------------------- | ---------------------------------------------------------------- | --------------------------------------------- |
| `normalize_trigger` | 把定时触发与规则触发统一为标准 TriggerEvent；非法触发直接终止                            | `analysis/schemas.py`                         |
| `build_state`       | 初始化 State：生成 task_id、补全时间窗口默认值                                   | —                                             |
| `route`             | 条件边，按 trigger_type 分发到子图                                         | —                                             |
| `merge_result`      | 收敛子图产出：报告归一化为统一 report 结构                                        | —                                             |
| `alert_decision`    | 判断是否产生预警：规则子图 severity ≥ high 必出预警；定时子图 risk_level=high 出预警；调用去重 | `alert_check_duplicate`、`alert_chain`（生成预警文案） |
| `persist_result`    | 写报告 / 写预警，记录 persist_result                                      | `analysis_write_report`、`alert_write_event`   |


### 2.4 定时任务子图（graph_scheduled.py）

定位：平台周期体检 + 业务洞察。触发：`scheduler.py` 每 15 分钟（可配置）。

```text
build_time_window
  -> plan_queries                 # ES Query Planner
  -> aggregate_metrics            # 并行：流量/错误/耗时/漏斗 四路聚合
  -> sample_logs                  # 拉取代表性样本（ERROR 优先 + 高峰段样本）
  -> build_evidence               # Evidence Builder 压缩证据包
  -> analyze_relations            # relation_chain：隐藏关系发现（LLM）
  -> generate_report              # report_chain：周期报告生成（LLM）
  -> 返回主图
```


| 节点                  | 是否用 LLM                | 依赖工具                                                | 依赖 Chain           |
| ------------------- | ---------------------- | --------------------------------------------------- | ------------------ |
| `build_time_window` | 否                      | —                                                   | —                  |
| `plan_queries`      | 否（第一版规则产出查询计划，不交给 LLM） | `field_catalog`                                     | —                  |
| `aggregate_metrics` | 否（纯 ES 聚合）             | `es_aggregate_metrics`（内部走 aggregation_service 六模板） | —                  |
| `sample_logs`       | 否                      | `es_search_logs`                                    | —                  |
| `build_evidence`    | 否（代码压缩）                | —                                                   | `evidence_builder` |
| `analyze_relations` | **是**                  | —                                                   | `relation_chain`   |
| `generate_report`   | **是**                  | —                                                   | `report_chain`     |


降级路径：LLM 不可用时，`analyze_relations` 跳过、`generate_report` 退化为模板拼接的纯统计报告（risk_level 由规则给出），保证定时报告永远有产出。

### 2.5 规则任务子图（graph_rule.py）

定位：关键错误即时深挖。触发：`trigger_scanner.py` 周期扫描 ES 中 `trigger_subgraph=True` 规则命中的日志（第一版轮询 30s，后续可演进为消费 Kafka 告警 topic）。

```text
parse_trigger_event
  -> fetch_context                # 并行四路上下文查询
  |     ├── 同 trace 日志
  |     ├── 同服务窗口日志
  |     ├── 同用户近期行为
  |     └── 同类错误分布
  -> correlate_events             # 代码层关联：时间排序、跨服务对齐、频次统计
  -> build_evidence               # 证据包压缩
  -> infer_root_cause             # diagnosis_chain：根因推断（LLM）
  -> assess_severity              # 规则 + LLM 置信度合成最终 severity
  -> generate_event_report        # 事件诊断报告
  -> 返回主图
```


| 节点                      | 是否用 LLM                            | 依赖工具                                                                              | 依赖 Chain           |
| ----------------------- | ---------------------------------- | --------------------------------------------------------------------------------- | ------------------ |
| `parse_trigger_event`   | 否                                  | `rule_match_log`（复核触发合法性）                                                         | —                  |
| `fetch_context`         | 否                                  | `es_get_trace_context`、`es_get_service_window`、`es_get_similar_errors`、（P2）用户行为查询 | —                  |
| `correlate_events`      | 否                                  | —                                                                                 | —                  |
| `build_evidence`        | 否                                  | —                                                                                 | `evidence_builder` |
| `infer_root_cause`      | **是**                              | —                                                                                 | `diagnosis_chain`  |
| `assess_severity`       | 部分（规则定级为主，LLM confidence 参考）       | —                                                                                 | —                  |
| `generate_event_report` | **是**（与 infer_root_cause 可合并为一次调用） | —                                                                                 | `diagnosis_chain`  |


### 2.6 Agent 中间层组件需求清单

把技术目标文档中的中间组件落到具体文件与开发优先级：


| 中间层组件               | 落点文件                                                    | 职责                                               | 优先级        |
| ------------------- | ------------------------------------------------------- | ------------------------------------------------ | ---------- |
| Trigger Event 标准化   | `analysis/schemas.py`                                   | 统一定时/规则两种触发输入                                    | P0         |
| Graph State         | `analysis/state.py`                                     | 全图状态契约                                           | P0         |
| Main Router         | `graph_main.py` 条件边                                     | 触发类型路由                                           | P0         |
| ES Query Planner    | `graph_scheduled.py` / `graph_rule.py` 内节点函数            | 按任务产出受控查询计划（第一版规则实现）                             | P0         |
| Metrics Aggregator  | `elasticsearch/aggregation_service.py`（复用，不在图内重写）       | 统计计算全部由代码完成                                      | P0（属第 1 章） |
| Evidence Builder    | `langchain/evidence_builder.py`                         | 原始日志 → 过滤 → 分组 → 采样 → 证据包；控制进入 LLM 的 token 量     | P0         |
| LLM Manager         | `langchain/llm_manager.py`                              | 多模型、API Key、参数、重试统一管理；`get_llm(task=...)` 按任务选模型 | P0         |
| Output Parser       | `langchain/output_parsers.py`                           | Pydantic 结构化输出 + 格式错误自动重试（轻量模型修 JSON）            | P0         |
| Prompt 管理           | `langchain/prompts.py`                                  | 周期报告 / 根因诊断 / 关系发现 / 预警解释 / 证据摘要五类 Prompt 集中管理   | P0         |
| Relation Analyzer   | `langchain/relation_chain.py`                           | 发现"高峰后支付失败上升"类隐藏关系                               | P1         |
| Alert Decider       | `graph_main.py` 节点 + `alert/dedup.py`                   | 预警判定与去重                                          | P1         |
| Persistence Writer  | `report/report_service.py`、`alert/alert_service.py`（复用） | 结果落地                                             | P1（属第 1 章） |
| Dedup / Idempotency | `alert/dedup.py` + State 的 task_id                      | 防同一错误反复触发重复报告                                    | P1         |
| Status Tracker      | State 的 `node_trace` + `analysis/schemas.py`            | 记录 running/success/failed/skipped，供前端展示          | P1         |
| Scheduler           | `analysis/scheduler.py`                                 | 定时触发入口，窗口对齐与防重叠运行                                | P1         |
| Trigger Scanner     | `analysis/trigger_scanner.py`                           | 扫描 ES 命中规则的新日志，去重后触发规则子图                         | P1         |


### 2.7 LangChain 层配置扩展

`core/config.py` 新增（与 LangChain 技术目标文档一致）：

```env
LLM_PROVIDER=openai            # 或 dashscope 等兼容供应商
LLM_API_KEY=
LLM_BASE_URL=
LLM_DEFAULT_MODEL=gpt-4o-mini  # 报告/预警解释/JSON 修复
LLM_ANALYSIS_MODEL=gpt-4o      # 根因诊断/关系发现
LLM_TIMEOUT_SECONDS=30
LLM_TEMPERATURE=0.2
ANALYSIS_SCHEDULE_MINUTES=15   # 定时子图周期
TRIGGER_SCAN_SECONDS=30        # 规则扫描周期
```

### 2.8 开发顺序（图相关）

```text
第 1 步（P0）：llm_manager + prompts + output_parsers + evidence_builder
              └── 验收：独立单测可跑通一次结构化 LLM 调用
第 2 步（P0）：report_chain + diagnosis_chain
              └── 验收：给定 mock 证据包能产出符合 schema 的报告
第 3 步（P0）：state + graph_scheduled 最小版（聚合 -> 证据 -> 报告，跳过关系发现）
              └── 验收：手动触发能写出一份周期报告
第 4 步（P1）：graph_rule 最小版 + trigger_scanner
              └── 验收：注入一条 PAY_FAIL 日志能自动产出事件诊断
第 5 步（P1）：graph_main 收敛 + alert 决策与去重 + scheduler 常驻
第 6 步（P2）：relation_chain 接入定时子图 + node_trace 前端展示
```

---

## 3. MCP 工具封装规划

### 3.1 封装原则

1. **工具只包装 services，不重新实现**：每个 MCP 工具是对应 service 函数的薄适配层（参数校验 + 调用 + 结果裁剪），业务逻辑留在 services 域；
2. **受控白名单**：工具入参全部为结构化枚举/受限参数（依托 field_catalog），LLM 不能传入裸 DSL、不能指定任意索引、不能取消 limit；
3. **读写分离**：查询类工具对 Agent 全开放；写入类工具（写报告/写预警）只允许图的 persist 节点调用，不进入 LLM 可自由选择的工具列表；
4. **双形态注册**：同一套工具函数在 `tools/registry.py` 中同时注册为：
  - 进程内 LangChain `StructuredTool`（第一阶段，图节点直接调用，无网络开销）；
  - 标准 MCP Server（第二阶段，基于 FastMCP 暴露，供外部 Agent / Cursor / 其他客户端复用）。

目录落点：

```text
backend/app/services/tools/
├── __init__.py
├── registry.py             # 工具注册中心：LangChain Tool 与 MCP Server 双形态出口
├── elasticsearch_tools.py  # 5 个 ES 查询/聚合/上下文工具
├── report_tools.py         # 报告写入与查询工具
├── alert_tools.py          # 预警写入/去重/查询工具
├── rule_tools.py           # 规则匹配工具
└── system_tools.py         # 系统健康检查工具
```

### 3.2 需要封装的 services 清单（回答"多少个"）

**结论：第一阶段封装 4 个 service 域、共 10 个工具；第二阶段扩展 6 个工具；3 个 service 域明确不封装。**

#### 第一阶段：10 个核心工具


| #   | MCP 工具                  | 包装的 service 函数                                                                | 类型    | 供哪些节点使用                        |
| --- | ----------------------- | ----------------------------------------------------------------------------- | ----- | ------------------------------ |
| 1   | `es_search_logs`        | `elasticsearch/log_query_service.search_logs`                                 | 读     | 定时子图 sample_logs               |
| 2   | `es_aggregate_metrics`  | `elasticsearch/aggregation_service`（六模板统一入口）                                  | 读     | 定时子图 aggregate_metrics         |
| 3   | `es_get_trace_context`  | `elasticsearch/context_service.get_trace_context`                             | 读     | 规则子图 fetch_context             |
| 4   | `es_get_service_window` | `elasticsearch/context_service.get_service_window`                            | 读     | 规则子图 fetch_context             |
| 5   | `es_get_similar_errors` | `elasticsearch/context_service.get_similar_errors`                            | 读     | 规则子图 fetch_context             |
| 6   | `analysis_write_report` | `report/report_service.write_report`                                          | **写** | 主图 persist_result              |
| 7   | `alert_write_event`     | `alert/alert_service.write_alert`                                             | **写** | 主图 persist_result              |
| 8   | `alert_check_duplicate` | `alert/dedup.check_duplicate`                                                 | 读     | 主图 alert_decision              |
| 9   | `system_health_check`   | `elasticsearch/cluster_status` + `kafka/cluster_status` + `docker_status`（组合） | 读     | 主图 normalize_trigger（链路不健康时降级） |
| 10  | `rule_match_log`        | `diagnosis/rule_engine.match_log`                                             | 读     | 规则子图 parse_trigger_event       |


#### 第二阶段：6 个增强工具


| #   | MCP 工具                    | 包装的 service 函数                                  | 用途                  |
| --- | ------------------------- | ----------------------------------------------- | ------------------- |
| 11  | `es_get_business_funnel`  | `aggregation_service.aggregate_behavior_funnel` | 行为漏斗洞察              |
| 12  | `es_detect_traffic_peak`  | `aggregation_service.aggregate_traffic`（峰值识别封装） | 请求高峰定位              |
| 13  | `es_compare_time_windows` | `aggregation_service`（双窗口对比封装）                  | 环比变化分析              |
| 14  | `kibana_generate_link`    | 新增轻量工具函数（拼 Kibana Discover URL）                 | 报告附跳转链接             |
| 15  | `report_list_recent`      | `report/report_service.list_recent_reports`     | 外部 Agent / 前端读取历史报告 |
| 16  | `alert_list_active`       | `alert/alert_service.list_active_alerts`        | 外部 Agent / 前端读取活跃预警 |


#### 明确不封装为 Agent 工具的 services


| service                    | 不封装原因                                       |
| -------------------------- | ------------------------------------------- |
| `simulation/`（日志生成）        | 数据源生产能力，Agent 调用会污染分析对象；只由 task 层使用         |
| `kafka/producer`           | 写消息队列属于数据注入，不应让 Agent 触达                    |
| `pipeline_verification.py` | 受控运维验证任务（起子进程），暴露给 Agent 有失控风险；仅供系统页 API 使用 |
| `diagnosis/analyzer.py`    | 它是图的调用方（门面），封装成工具会造成"图调用图"的循环依赖             |


### 3.3 工具 Schema 约定

每个工具必须定义 Pydantic 入参/出参模型（放在 `tools/` 各文件内，复用 `schemas/log.py` 的枚举）：

```python
class EsAggregateMetricsInput(BaseModel):
    template: Literal["traffic", "errors", "latency", "behavior_funnel",
                      "security", "infra_health"]
    log_types: Optional[List[LogType]] = None      # 受 field_catalog 校验
    start_time: datetime
    end_time: datetime
    group_by: Optional[AggregateField] = None
    interval: Optional[TimeInterval] = None
    top_n: int = Field(default=10, le=50)          # 硬上限
```

约束要求：

1. 所有时间窗口入参强制必填且最大跨度受限（默认不超过 24 小时）；
2. 所有返回结果限制条数（样本日志默认 50 条上限，聚合桶 50 个上限）；
3. 工具内部捕获 ES 异常，返回 `{"ok": false, "error": ...}` 结构化错误，绝不向图抛裸异常；
4. 每次工具调用记录 `task_id + tool_name + 耗时` 到 State 的 `node_trace`，保证分析结果可追溯。

### 3.4 MCP Server 形态（第二阶段）

- 基于 FastMCP 在 `tools/registry.py` 暴露 `create_mcp_server()`，新增 task `app/tasks/run_mcp_server.py` 独立运行；
- 仅暴露读类工具（1-5、8-10、11-16），写类工具（6、7）不对外部 MCP 客户端开放；
- 价值：答辩时可演示"同一套日志分析工具既支撑内部 LangGraph，又能被 Cursor 等外部 Agent 直接调用"。

---

## 4. 总体里程碑路线


| 里程碑              | 内容                                                                                   | 涉及章节    | 验收标准                                  |
| ---------------- | ------------------------------------------------------------------------------------ | ------- | ------------------------------------- |
| M1 数据底座完善        | field_catalog + index_service 按 log_type 拆索引 + aggregation_service + context_service | 1.2     | 六类聚合模板对真实 ES 数据返回正确结果                 |
| M2 工具层成型         | tools/ 第一阶段 10 个工具 + registry（LangChain Tool 形态）                                     | 3.2     | 单测中工具可独立调用并返回结构化结果                    |
| M3 LangChain 能力层 | llm_manager + prompts + output_parsers + evidence_builder + 两个核心 Chain               | 2.6/2.7 | mock 证据包可产出符合 schema 的报告              |
| M4 定时子图闭环        | graph_scheduled 最小版 + scheduler + report 持久化                                         | 2.4     | 每 15 分钟自动写出一份周期报告到 analysis-results-* |
| M5 规则子图闭环        | graph_rule 最小版 + trigger_scanner + alert 持久化与去重                                      | 2.5     | 注入 PAY_FAIL 日志后自动产出事件诊断与预警            |
| M6 主图收敛与前端展示     | graph_main + reports/alerts API + node_trace 展示                                      | 2.3/1.3 | 前端可见最新报告、活跃预警与图执行轨迹                   |
| M7 增强项           | relation_chain、第二阶段工具、MCP Server 形态                                                  | 2.4/3.4 | 演示隐藏关系发现与外部 Agent 调用                  |


依赖关系：M1 → M2 → M3 →（M4 与 M5 可并行）→ M6 → M7。其中 M1 是一切的前提；M3 失败不阻塞 M4 的降级版（纯统计报告）。

---

## 5. 基础设施依赖声明

以下事项后端只能预留接口，链路接通需基础设施层配合（不属于本规划的修改范围）：

1. Logstash output 按 `log_type` 路由到 `app-logs-{log_type}-`* 索引（当前为单一索引写入）；
2. `analysis-results-*` 与 `alerts-*` 索引的创建可由后端 `index_service` 完成，但需要 ES 账号具备索引管理权限；
3. LLM API Key 与可访问的模型服务（无 Key 时 M3 之后所有 LLM 节点走降级路径）；
4. 若规则触发演进为 Kafka 告警 topic 消费，需要 Logstash/后端新增消费配置。

