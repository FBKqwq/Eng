# Analysis（LangGraph 编排层）DEV 文档

## 1. 文档用途说明

维护 `app/services/analysis/` LangGraph 流程编排层。负责主图路由、定时子图、规则子图、调度与触发扫描；不得直接拼 ES DSL。

> **M7 收口说明**：M7-04 已将 `analyze_relations` 纳入定时子图七节点流；**M7 完成即总体规划（M1~M7）全部收口**（测试收口见 M7-09）。

## 2. 模块总览

| 文件 | 职责 | 状态 |
|---|---|---|
| `state.py` | 统一 `AnalysisState` TypedDict；`create_initial_state` / `append_node_trace` / `record_error` | 已实现（M4 最小版） |
| `schemas.py` | `TriggerEvent`、`NodeTraceEntry`；`normalize_trigger` / `make_node_trace` | 已实现（M4 最小版） |
| `graph_scheduled.py` | 定时子图：周期体检（七节点 LangGraph，含 analyze_relations） | 已实现（M4 + M7-04） |
| `scheduler.py` | 定时触发（`analysis_schedule_minutes`）；`run_once` 委托 `run_main_graph("scheduled")` | 已实现（M6 收敛） |
| `graph_rule.py` | 规则子图：事件深挖（七节点 LangGraph） | 已实现（M5 最小版） |
| `trigger_scanner.py` | 规则扫描触发（`trigger_scan_seconds` 轮询）；`scan_once` 委托 `run_main_graph("rule")` | 已实现（M6 收敛） |
| `graph_main.py` | 主图：路由、收敛、预警决策、持久化收口 | 已实现（M6） |

## 3. 模块职责边界

- 应该放在这里：图状态、节点编排、条件分支、node_trace 记录。
- 不应该放在这里：ES 聚合实现、LLM Prompt、HTTP API。

## 4. 已实现功能清单

- `AnalysisState` 字段契约与辅助函数（`state.py`）。
- 触发标准化：`normalize_trigger` 支持 `scheduled` / `rule` 两种类型；`make_node_trace` 构造节点追踪记录（`schemas.py`）。
- **定时子图**（`graph_scheduled.py`，M7-04 升级七节点）：LangGraph `StateGraph` 七节点线性编排，可独立 `invoke`。
- **主图**（`graph_main.py`，M6）：LangGraph 七节点编排；`run_main_graph(trigger_type, **kwargs)` 返回 `{ ok, report_id, alert_id, node_trace, alert_decision, errors }`；报告与预警写入仅在 `persist_result` 节点收口。
- **调度器**（`scheduler.py`，M6 收敛）：`run_once` 委托 `run_main_graph("scheduled")`，不再直接 `write_report`；`start_scheduler` / `stop_scheduler` 基于 APScheduler（`max_instances=1` 防重叠）。
- 独立任务入口：`app/tasks/run_scheduler.py`（`--once` 或常驻模式，仅调 scheduler）。
- 独立扫描入口：`app/tasks/run_trigger_scanner.py`（`--once` 或常驻模式，仅调 trigger_scanner）（M5-08）。
- **规则子图**（`graph_rule.py`，M5）：七节点 LangGraph；`run_rule_subgraph(trigger_event)` 返回 `{ ok, report, alert_candidate, node_trace, errors }`；不负责持久化。
- **规则扫描器**（`trigger_scanner.py`，M6 收敛）：`scan_once` 扫描 ES → `match_log` 复核 → 逐条委托 `run_main_graph("rule", trigger_event=...)`；不再在 scanner 内直接持久化或去重（由主图 `alert_decision` + `persist_result` 收口）；`start_trigger_scanner` / `stop_trigger_scanner` 基于 APScheduler（`max_instances=1`）。

### 4.1 定时子图节点流（M4 + M7-04）

```text
build_time_window → plan_queries → aggregate_metrics → sample_logs
                  → build_evidence → analyze_relations → generate_report → END
```

| 节点 | 职责 | 降级行为 |
|---|---|---|
| `build_time_window` | 校验并丰富 `time_window`（start/end/duration_seconds） | 失败记入 errors，继续下游 |
| `plan_queries` | 固定六类聚合模板 + 样本策略写入 `query_plan` | 失败时空 plan，继续 |
| `aggregate_metrics` | 调 `es_aggregate_metrics` 逐模板聚合 | 单模板失败记入 errors，其余继续 |
| `sample_logs` | ERROR/CRITICAL 优先采样，不足补通用样本，去重 ≤ 50 | ES 不可用记入 errors，继续 |
| `build_evidence` | 调 `evidence_builder.build_evidence_package` | 失败时最小空证据包 |
| `analyze_relations` | 调 `relation_chain.discover_relations`，写入 `state.relations` | 见下方 **4.1.1** |
| `generate_report` | 调 `report_chain.generate_periodic_report`，注入 relations | 失败时 `degraded=True` 失败报告；relations 非空时仍注入 |

- **聚合模板**（`plan_queries` 固定）：`traffic`、`errors`、`latency`、`behavior_funnel`、`security`、`infra_health`。
- **样本策略**：优先 ERROR/CRITICAL 日志（上限 30），不足时补通用样本（上限 20），去重后总量 ≤ 50。

#### 4.1.1 `analyze_relations` 节点与 relations 注入（M7-04）

1. 输入：`state.evidence_package`（由 `build_evidence` 产出）。
2. 调用：`discover_relations(package)` → 写入 `state.relations`（`list[dict]`）。
3. **node_trace 状态**：
   - 发现关系 → `success`，摘要含关系条数。
   - LLM 降级或空列表 → `skipped`（摘要「关系发现降级，空关系列表」或「未发现隐藏关系」）；**不阻断** `generate_report`。
   - 异常 → `failed`，`relations` 置 `[]`，仍继续下游。
4. **报告注入**（`generate_report`）：
   - 有 relations 时：`report_input = {**evidence, "relations": relations}`，且 `analysis_report["relations"] = relations`。
   - 无 relations 时：仅传 evidence，报告照常产出。

### 4.2 规则子图节点流（M5）

```text
parse_trigger_event → fetch_context → correlate_events → build_evidence
                    → infer_root_cause → assess_severity → generate_event_report → END
```

| 节点 | 职责 | 降级行为 |
|---|---|---|
| `parse_trigger_event` | 调 `match_log` 复核触发日志，写入 `query_plan.rule_match` | 未命中或未标 `trigger_subgraph` 时记录 warning，继续深挖 |
| `fetch_context` | `get_trace_context` / `get_service_window` / `get_similar_errors` 采集上下文 | 单路 ES 失败记入 errors，其余继续；`raw_logs` 去重合并 |
| `correlate_events` | 时间线排序、跨服务统计，写入 `relations` 与 `metrics.correlation` | 失败时空 relations + 零计数 metrics |
| `build_evidence` | 调 `evidence_builder.build_evidence_package` | 失败时最小空证据包 |
| `infer_root_cause` | 调 `diagnosis_chain.infer_root_cause` | 失败时降级根因结构写入 `query_plan` |
| `assess_severity` | 规则定级 + LLM 置信度合成 `final_severity`；组装 `alert_candidate` | 失败时 medium 降级预警候选 |
| `generate_event_report` | 调 `report_chain.generate_event_report`，合并定级与根因 | 失败时 `degraded=True` 失败报告 |

- 上下文窗口：触发时间前 15 分钟、后 5 分钟。
- 子图返回 `ok` 以 `analysis_report` 非空为准；持久化由主图 `persist_result` 收口（M6 前由 `trigger_scanner` 负责，已迁移）。

### 4.3 trigger_scanner scan_once 闭环（M6 收敛）

```text
_fetch_candidate_logs（最近 trigger_scan_seconds 窗口内 ERROR/CRITICAL）
        │
        ▼  按 log_id 本轮去重（seen_log_ids）
   match_log 复核（须 matched=True 且 trigger_subgraph=True）
        │
        ▼
   run_main_graph("rule", trigger_event=...)
        │
        └─ 主图内 persist_result 写 report + alert（含去重）
```

- `scan_once` 返回：`{ ok, triggered_count, alert_ids, report_ids [, errors] }`。
- 周期调度：`settings.trigger_scan_seconds`（默认 30s）；`max_instances=1` 防重叠执行。
- 候选日志查询：最近一个扫描窗口内的 ERROR/CRITICAL，最多 100 条，按 timestamp 降序。

### 4.4 主图节点流与持久化收口（M6）

```text
normalize_trigger → build_state → route（条件分支）
        ├─ scheduled → run_scheduled_subgraph ─┐
        ├─ rule      → run_rule_subgraph      ─┤
        └─ invalid   ──────────────────────────┘
                              ▼
                    merge_result
                              ▼
                    alert_decision（去重 + explain_alert）
                              ▼
                    persist_result（write_report + write_alert）
                              ▼
                            END
```

| 节点 | 职责 | 降级行为 |
|---|---|---|
| `normalize_trigger` | 调 `normalize_trigger` 标准化触发入参 | 失败标记 `trigger_valid=False`，路由至 `invalid` 分支 |
| `build_state` | 初始化 `task_id` 与各状态槽位 | 失败记录 error，继续下游 |
| `run_scheduled_subgraph` | 调 `run_scheduled_subgraph` | 子图失败时降级空报告，合并子图 `node_trace`（前缀 `scheduled.`） |
| `run_rule_subgraph` | 调 `run_rule_subgraph` | 子图失败时降级空报告/候选，合并子图 `node_trace`（前缀 `rule.`） |
| `merge_result` | 归一化 `analysis_report`，合并子图轨迹 | 无报告时生成 fallback 报告 |
| `alert_decision` | 按触发类型决策是否出预警；`check_duplicate`；调 `explain_alert` 写文案 | 失败记录 error，跳过预警 |
| `persist_result` | **唯一持久化收口**：`write_report` + 条件 `write_alert`（去重累加或新建） | 单路写入失败记入 errors，不抛异常 |

- `run_main_graph` 返回：`{ ok, report_id, alert_id, node_trace, alert_decision, errors }`；`ok` 以 `report_write_ok` 且 `report_id` 非空为准。
- 预警决策：`rule` 路径 severity ≥ high 出预警；`scheduled` 路径 `risk_level == high` 出预警。
- 子图内**禁止**写 ES；scheduler / trigger_scanner **禁止**直接 `write_report` / `write_alert`（M6 后）。

### 4.5 节点级降级策略（M4/M5/M6/M7 通用）

各节点采用 **捕获异常 → `record_error` → `append_node_trace(failed|skipped)` → 继续下游** 模式，整图不因单节点失败而崩溃。

子图返回：`{ ok, report[, alert_candidate], node_trace, errors }`。

## 5. 待开发功能清单

- P3：`test_m7_enhancements` 覆盖七节点定时子图与 relations 注入（M7-09）。

## 6. 模块状态表

| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| `schemas` | 已实现（M4 + 时区修复） | 2026-06-23 | elk-backend-agent (e2e) | 低 | `_default_time_window` 改用 UTC aware 时间 |
| `state` | 已实现（M4 最小版） | 2026-06-22 | elk-backend-agent (M4-03) | 低 | create_initial_state / append_node_trace / record_error |
| `graph_scheduled` | 已实现（M7-04 七节点） | 2026-06-22 | 定时子图 Agent (M7-04) | 低 | 含 analyze_relations；relations 注入报告 |
| `scheduler` | 已实现（M6 收敛） | 2026-06-22 | elk-backend-agent (M6-03) | 低 | run_once 委托 run_main_graph |
| `graph_rule` | 已实现（M5 最小版） | 2026-06-22 | M5-06 Agent | 中 | 七节点；节点降级不中断 |
| `trigger_scanner` | 已实现（M6 收敛） | 2026-06-22 | elk-backend-agent (M6-04) | 低 | scan_once 委托主图；无直接持久化 |
| `graph_main` | 已实现（M6） | 2026-06-22 | elk-backend-agent (M6-02) | 低 | 七节点主图；persist_result 唯一写库收口 |
| Analysis 层整体 | M4 定时 + M5 规则 + M6 主图 + M7 关系节点完成 | 2026-06-22 | 文档 Agent (M7-10) | 低 | 定时子图七节点已对齐总体规划 |

## 7. 禁止重复实现清单

| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| ES 聚合 | `tools/elasticsearch_tools.es_aggregate_metrics` | 禁止在图节点内重写 DSL |
| 日志查询 | `elasticsearch/log_query_service` | 禁止图节点绕过 service 直连 client |
| 证据构建 | `langchain/evidence_builder` | 禁止在节点内重复采样逻辑 |
| 关系发现 | `langchain/relation_chain.discover_relations` | 禁止在 `analyze_relations` 节点内直接调 LLM |
| 报告生成 | `langchain/report_chain` | 禁止在节点内直接调 LLM |
| 报告持久化 | `analysis/graph_main.py` → `persist_result` 节点 | 禁止在子图、scheduler、trigger_scanner 内写 ES（M6 后） |
| 预警去重 | `alert/dedup.py`（主图 `alert_decision` 调用） | 禁止在 trigger_scanner 外重复实现幂等查重 |
| 规则匹配 | `diagnosis/rule_engine.match_log` | 禁止在 graph_rule 内硬编码规则 |
| 工具调用 | `tools/` 薄适配层 | 禁止图节点绕过 tools 直连 service |

## 8. 真实实现与设计愿景差异

| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 一主图+两子图 | LangGraph 主图路由 scheduled/rule 两子图并收敛 | M6 `graph_main` 七节点真实跑通；scheduler/scanner 均委托主图 | — |
| 关系发现 | `analyze_relations` 纳入定时分析链路 | M7-04 已纳入定时子图；降级 skipped 不阻断报告 | M7-09 补单测 |
| 预警决策 | 主图 `alert_decision` 节点 | M6 已实现：规则定级 + 去重 + `explain_alert` | — |
| 触发扫描 | 周期轮询 ES 命中规则日志 | `trigger_scanner` 委托主图；持久化收口于 `persist_result` | — |

## 9. 开发日志区

| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-06-16 | 建立 analysis 七文件占位骨架 | `app/services/analysis/*.py` | 骨架就绪 | 已由 M4/M5 实现 |
| 2026-06-22 | M4-02~07：定时子图 + 调度器 | `schemas.py`、`state.py`、`graph_scheduled.py`、`scheduler.py` | M4 定时闭环可用 | — |
| 2026-06-22 | M4-09：DEV 文档收敛（M4 部分） | `analysis/DEV.md` | 定时子图节点流、降级策略已记录 | 规则子图待 M5 |
| 2026-06-22 | M5-06：规则子图七节点 | `graph_rule.py` | run_rule_subgraph 返回 report+alert_candidate+node_trace | ES/LLM 需集成环境验证 |
| 2026-06-22 | M5-07：trigger_scanner 闭环 | `trigger_scanner.py` | scan_once 扫描→子图→写报告+去重预警 | — |
| 2026-06-22 | M5-08：扫描 task 入口 | `tasks/run_trigger_scanner.py` | `--once` 与常驻模式 | — |
| 2026-06-22 | M5-09：M5 全 mock 测试 | `tests/test_m5_rule.py` | 16 passed；规则/预警/子图/闭环覆盖 | — |
| 2026-06-22 | M5-10：DEV 文档收敛（M5 部分） | `analysis/DEV.md` | 规则子图节点流、scan_once 闭环与去重已记录 | graph_main M6 |
| 2026-06-22 | M6-02：主图七节点收敛 | `graph_main.py` | normalize→route→子图→merge→alert_decision→persist | — |
| 2026-06-22 | M6-03/04：scheduler/scanner 委托主图 | `scheduler.py`、`trigger_scanner.py` | 移除直接 write_report/write_alert | — |
| 2026-06-22 | M6-07：DEV 文档收敛（M6 部分） | `analysis/DEV.md` | 主图节点流、持久化收口、委托关系已记录 | — |
| 2026-06-22 | M7-04：定时子图七节点 + analyze_relations | `graph_scheduled.py` | relations 写 state 并注入报告；降级 skipped | — |
| 2026-06-22 | **M7-10：文档收口** | `analysis/DEV.md` | 七节点流、relations 注入/降级已记录；移除 M7 待实现措辞 | 单测见 M7-09 |
| 2026-06-23 | **真实 ELK 端到端联调 + 时区 bug 修复** | `schemas.py`、`graph_scheduled.py`、`graph_rule.py`、`graph_main.py` | `_default_time_window` 原用 naive 本地 `datetime.now()`，isoformat 无时区后缀被 ES 当 UTC 解释，在 UTC+8 造成定时窗口整体偏移 8 小时、聚合/采样恒为空（report degraded=False 但 total_logs=0）；改为 `datetime.now(timezone.utc)`，并将 graph_rule 上下文窗口 anchor 兜底、各处 recorded_at/created_at 统一为 UTC。修复后定时主图采样 31 条、发现 3 条关系、风险定级 high 并出预警；规则主图根因诊断 + 预警 + 去重幂等均真实跑通 | scheduler 默认窗口为 `analysis_schedule_minutes`（15min），一次性手动触发需确保数据在窗口内 |
