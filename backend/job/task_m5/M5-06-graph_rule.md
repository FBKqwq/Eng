# M5-06：规则子图最小版 graph_rule

## Agent 角色

规则子图 Agent — 实现事件深挖流：上下文→关联→证据→根因→定级→事件报告。

## 唯一负责文件

```
app/services/analysis/graph_rule.py
```

## 禁止修改

- `state.py`、`schemas.py`（只 import）
- `context_service.py`、`evidence_builder.py`、`diagnosis_chain.py`、`rule_engine.py`（只 import）
- `graph_scheduled.py`、`graph_main.py`、`trigger_scanner.py`

## 前置依赖

- M5-04 为 `已完成`/`已合并`

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.analysis.state import create_initial_state, append_node_trace; from app.services.analysis.schemas import normalize_trigger; from app.services.diagnosis.rule_engine import match_log; from app.services.elasticsearch.context_service import get_trace_context, get_service_window, get_similar_errors; from app.services.langchain.evidence_builder import build_evidence_package; from app.services.langchain.diagnosis_chain import infer_root_cause, generate_event_report; print('deps ok')"
```

## 开发要求

### 节点流
```text
parse_trigger_event -> fetch_context -> correlate_events -> build_evidence
  -> infer_root_cause -> assess_severity -> generate_event_report
```
- `parse_trigger_event`：调 `match_log` 复核触发合法性
- `fetch_context`：调 context_service 三入口（trace / service_window / similar_errors）
- `correlate_events`：代码层时间排序、跨服务对齐、频次统计（不调 LLM）
- `build_evidence`：`evidence_builder.build_evidence_package`
- `infer_root_cause` / `generate_event_report`：复用 `diagnosis_chain`（含降级）
- `assess_severity`：规则定级为主，LLM confidence 参考

### 实现方式
- 推荐 LangGraph `StateGraph(AnalysisState)`，与 graph_scheduled 一致风格
- 每节点 `append_node_trace`；失败 `record_error` 并降级，不中断

### `run_rule_subgraph(trigger_event: dict) -> dict`
- 经 `normalize_trigger` 标准化 rule 触发
- 返回 `{"ok": True, "report": ..., "alert_candidate": ..., "node_trace": [...], "errors": [...]}`
- **不负责持久化**（由 trigger_scanner 写库 + 去重）；无 placeholder

### `build_rule_graph()`
- 返回编译后的图对象

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `run_rule_subgraph` 对 PAY_FAIL 触发返回 report + alert_candidate + node_trace |
| AC-02 | ES/LLM mock 下跑通七节点 |
| AC-03 | 某节点异常走降级、errors 非空但整图不崩 |
| AC-04 | 无 placeholder |
| AC-05 | 更新 `task_m5/STATUS.md` 本行 |
