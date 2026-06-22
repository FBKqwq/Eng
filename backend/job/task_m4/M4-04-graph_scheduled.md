# M4-04：定时子图最小版 graph_scheduled

## Agent 角色

定时子图 Agent — 实现最小版定时分析流：聚合 → 证据 → 报告（跳过关系发现）。

## 唯一负责文件

```
app/services/analysis/graph_scheduled.py
```

## 可附加修改

```
requirements.txt   # 追加 langgraph（与 langchain-core 版本兼容）
```

## 禁止修改

- `state.py`、`schemas.py`（只 import）
- `aggregation_service.py`、`evidence_builder.py`、`report_chain.py`（只 import）
- `scheduler.py`、`graph_main.py`

## 前置依赖

- M4-02、M4-03 均为 `已完成`/`已合并`

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.analysis.state import create_initial_state, append_node_trace; from app.services.analysis.schemas import normalize_trigger; from app.services.langchain.evidence_builder import build_evidence_package; from app.services.langchain.report_chain import generate_periodic_report; print('deps ok')"
```

## 开发要求

### 节点流（最小版，跳过 analyze_relations）
```text
build_time_window -> plan_queries -> aggregate_metrics -> sample_logs
  -> build_evidence -> generate_report
```

### 实现方式
- 可用 LangGraph `StateGraph(AnalysisState)` 编译，或第一版用顺序函数链（推荐 LangGraph 以对齐总体规划）
- `aggregate_metrics`：调用 `aggregation_service` 六模板（或 `es_aggregate_metrics` 工具）写入 `state["metrics"]`
- `sample_logs`：调 `log_query_service.search_logs` / `es_search_logs` 取代表样本写入 `state["raw_logs"]`
- `build_evidence`：调 `evidence_builder.build_evidence_package`
- `generate_report`：调 `report_chain.generate_periodic_report`，写入 `state["analysis_report"]`
- 每节点用 `append_node_trace` 记录；失败 `record_error` 并降级，不中断

### `run_scheduled_subgraph(time_window=None) -> dict`
- 组装初始 state（经 `normalize_trigger` 标准化 scheduled 触发）
- 执行图，返回 `{"ok": True, "report": ..., "node_trace": [...], "errors": [...]}`
- **不负责持久化**（由 scheduler 调 report_service 写入）；无 placeholder

### `build_scheduled_graph()`
- 返回编译后的图对象（LangGraph）或可调用链

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `run_scheduled_subgraph` 返回含 report + node_trace，无 placeholder |
| AC-02 | ES/LLM mock 下跑通六节点 |
| AC-03 | 某节点异常时走降级、errors 非空但整图不崩 |
| AC-04 | requirements 含 langgraph |
| AC-05 | 更新 `task_m4/STATUS.md` 本行 |
