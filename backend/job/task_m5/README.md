# M5 规则子图闭环 — 任务编排说明

> 对应总体规划：`doc/后端开发总体规划-Services-LangGraph-MCP.md` §2.5 / §2.8（第 4 步）/ §1.3 alert·diagnosis 域（里程碑 **M5**）  
> 前置里程碑：**M1 数据底座** + **M2 工具层** + **M3 LangChain 能力层** + **M4 定时子图闭环**（四者 STATUS 须全绿）  
> 原则：**一个 Agent 只负责一个主脚本**，避免并行改同一文件

---

## 1. M5 目标

打通**规则触发闭环**：扫描器发现命中规则的日志 → 规则子图（上下文→证据→根因→事件报告）→ 报告持久化 + 预警写入（去重）。

| 项 | 说明 |
| --- | --- |
| **里程碑验收** | 注入一条 `PAY_FAIL` 日志后，扫描器自动触发规则子图，产出**事件诊断报告**与**预警事件**，并写入 `analysis-results-*` / `alerts-*` |
| **最小版范围** | 规则子图节点齐全；`infer_root_cause`/`generate_event_report` 复用 M3 `diagnosis_chain`，LLM 不可用时降级 |
| **不在 M5** | 主图收敛与统一预警决策（M6）、`relation_chain`（M7）、MCP Server（M7） |

---

## 2. M5 范围与组件

| 组件 | 落点文件 | 依赖 |
| --- | --- | --- |
| 声明式规则表 | `diagnosis/rule_definitions.py` | — |
| 规则匹配 | `diagnosis/rule_engine.py`（`match_log`） | rule_definitions |
| 预警持久化 | `alert/alert_service.py` | M1 `alerts-*` 模板 |
| 预警去重 | `alert/dedup.py` | M1 `alerts-*` 模板 |
| 规则子图最小版 | `analysis/graph_rule.py` | M2 context 工具、M3 evidence_builder/diagnosis_chain、M4 state/schemas、rule_engine |
| 预警 API | `api/v1/alerts.py` | alert_service |
| 触发扫描器 | `analysis/trigger_scanner.py` | graph_rule、alert_service、dedup、report_service |
| 扫描任务入口 | `tasks/run_trigger_scanner.py`（新建） | trigger_scanner |

**复用（不重写）**：`context_service`（trace/service_window/similar_errors）、`evidence_builder`、`diagnosis_chain`、`report_service`、`state`/`schemas`。

---

## 3. 任务清单与文件归属

| 任务编号 | 文档 | 唯一负责脚本 | 前置依赖 |
| --- | --- | --- | --- |
| M5-01 | M5-01-alert_service.md | `alert/alert_service.py` | M1 完成 |
| M5-02 | M5-02-dedup.md | `alert/dedup.py` | M1 完成 |
| M5-03 | M5-03-rule_definitions.md | `diagnosis/rule_definitions.py` | M1 完成 |
| M5-04 | M5-04-rule_engine.md | `diagnosis/rule_engine.py` | M5-03 |
| M5-05 | M5-05-alerts_api.md | `api/v1/alerts.py` | M5-01 |
| M5-06 | M5-06-graph_rule.md | `analysis/graph_rule.py` | M5-04 |
| M5-07 | M5-07-trigger_scanner.md | `analysis/trigger_scanner.py` | M5-06、M5-01、M5-02 |
| M5-08 | M5-08-run_trigger_scanner.md | `tasks/run_trigger_scanner.py`（新建） | M5-07 |
| M5-09 | M5-09-test_rule.md | `tests/test_m5_rule.py`（新建） | M5-06、M5-07 |
| M5-10 | M5-10-dev_docs.md | `diagnosis/DEV.md` + `alert/DEV.md` + `analysis/DEV.md` | M5-06、M5-07 |

**依赖说明**：

- `match_log` 升级为读取 `rule_definitions` 后，M2 工具 `rule_match_log`（已薄包装）自动透传真实结果，无需改 tools。
- `alerts-*` 索引模板已在 M1 `create_analysis_indices` 就绪，M5 不改 index_service。
- `core/config.py` 的 `trigger_scan_seconds` 已就绪，M5 不改 config。
- 无新增第三方依赖（langgraph/apscheduler 已在 M4 引入）。

---

## 4. 推荐执行顺序

```text
阶段 A（可并行，3 Agent）
├── M5-01  alert_service.py        alerts-* 读写
├── M5-02  dedup.py                去重幂等
└── M5-03  rule_definitions.py     声明式规则表

阶段 B（可并行，2 Agent）
├── M5-04  rule_engine.py（match_log）   依赖 M5-03
└── M5-05  alerts_api.py                 依赖 M5-01

阶段 C（串行）
└── M5-06  graph_rule.py                 依赖 M5-04

阶段 D（串行）
└── M5-07  trigger_scanner.py            依赖 M5-06、M5-01、M5-02

阶段 E（可并行，3 Agent）
├── M5-08  tasks/run_trigger_scanner.py  依赖 M5-07
├── M5-09  tests/test_m5_rule.py         依赖 M5-06、M5-07
└── M5-10  diagnosis/alert/analysis DEV  依赖 M5-06、M5-07
```

---

## 5. M5 总体验收（Definition of Done）

- [ ] `rule_definitions` 含阈值/错误码/频率三类规则；`PAY_FAIL` 规则 `trigger_subgraph=True`
- [ ] `match_log` 读取规则表，命中 `PAY_FAIL` 返回 `matched=True`、`severity`、`trigger_subgraph=True`
- [ ] `alert_service` 三函数真实读写 `alerts-*`，状态机 active→acknowledged，去除 placeholder
- [ ] `dedup.check_duplicate` 基于幂等键查重，重复时返回 existing_alert_id（累加 evidence_count）
- [ ] `run_rule_subgraph(trigger_event)` 跑通：上下文→证据→根因→事件报告，返回结构化结果 + node_trace
- [ ] `scan_once` 闭环：发现触发日志 → 子图 → 写报告 + 去重写预警（mock ES 验证调用）
- [ ] `GET /api/v1/alerts/active`、`POST /alerts/{id}/ack` 去占位返回真实结果
- [ ] `pytest tests/test_m5_rule.py` 全绿（ES/LLM 全 mock）
- [ ] `diagnosis/DEV.md`、`alert/DEV.md`、`analysis/DEV.md` 更新
- [ ] `task_m5/STATUS.md` 全部任务 `已完成`

---

## 6. 跨任务约定

1. 只改自己负责的脚本；无新增第三方依赖。
2. 不改 `index_service.py`、`core/config.py`、`context_service.py`、M3 langchain、M4 已实现文件（只 import）。
3. 图节点失败写 `state["errors"]` 并降级，不中断整图。
4. LLM 不可用时 `infer_root_cause`/`generate_event_report` 复用 `diagnosis_chain` 降级。
5. 持久化归属：`graph_rule` 只产出报告 + 预警候选；**trigger_scanner** 负责调 `report_service` / `alert_service` + `dedup`。
6. ES 写入异常返回结构化错误，不抛裸异常。
7. 中文注释与文档使用简体中文；不要 commit。
8. 进度维护见 `task_m5/STATUS.md`；派发 Prompt 见 `PROMPT_DISPATCH.md`。

---

## 7. 与后续里程碑关系

```text
M4 定时子图闭环 ┐
M5 规则子图闭环 ┘→ M6 主图收敛（graph_main 路由两子图 + 统一预警决策 + node_trace 前端展示）
                    ↘ M7 relation_chain + 第二阶段工具 + MCP Server
```

M5 完成后，M6 用 `graph_main` 将定时与规则两子图作为 subgraph 挂载，统一在 `persist_result` 节点收敛写库与预警决策。

---

## 8. 已知遗留（不阻塞 M5）

| 项 | 现状 | 何时收敛 |
| --- | --- | --- |
| `graph_main` 主图与统一预警决策 | 占位 | M6 |
| `analyze_relations` / `relation_chain` | 跳过 | M7 |
| `alert_chain` 预警文案解释 | 占位 | M6（可选） |
| MCP Server | 占位 | M7 |
| 真实 LLM 联调 | 需配置 `LLM_API_KEY` | 集成环境 |
