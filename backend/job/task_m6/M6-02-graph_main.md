# M6-02：主图收敛 graph_main

## Agent 角色

主图 Agent — 路由两子图，统一结果归一化、预警决策、持久化。

## 唯一负责文件

```
app/services/analysis/graph_main.py
```

## 禁止修改

- graph_scheduled / graph_rule / state / schemas / alert_chain / dedup / report_service / alert_service（只 import）
- scheduler、trigger_scanner

## 前置依赖

- M6-01 为 `已完成`/`已合并`

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.analysis.graph_scheduled import run_scheduled_subgraph; from app.services.analysis.graph_rule import run_rule_subgraph; from app.services.analysis.state import create_initial_state, append_node_trace; from app.services.analysis.schemas import normalize_trigger; from app.services.alert.dedup import check_duplicate; from app.services.alert.alert_service import write_alert; from app.services.report.report_service import write_report; from app.services.langchain.alert_chain import explain_alert; print('deps ok')"
```

## 开发要求

### 节点流（§2.3）
```text
normalize_trigger -> build_state -> route
  ├── scheduled -> run_scheduled_subgraph
  └── rule      -> run_rule_subgraph
  -> merge_result -> alert_decision -> persist_result -> END
```

- `route`：LangGraph 条件边按 `trigger_type` 分发
- `merge_result`：子图 report 归一化为统一结构；汇总子图 `node_trace` 到主图 state
- `alert_decision`：规则 severity≥high / 定时 risk_level=high 触发预警候选；调 `dedup.check_duplicate`；`alert_chain.explain_alert` 生成文案；写入 `state["alert_decision"]`
- `persist_result`：`report_service.write_report`（report 内嵌 `node_trace`）；若需预警且未重复，`alert_service.write_alert`

### `run_main_graph(trigger_type, **kwargs) -> dict`
- 返回 `{"ok": True, "report_id": ..., "alert_id": ...|None, "node_trace": [...], "alert_decision": {...}, "errors": [...]}`
- 节点失败写 errors 并降级，不中断；无 placeholder

### `build_main_graph()`
- 返回编译后的 LangGraph 主图（子图作为节点挂载）

### 约定
- 持久化只在 `persist_result` 发生（收口）
- 不要 commit

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | scheduled 触发跑通并 persist 报告，返回 node_trace |
| AC-02 | rule 触发跑通并 persist 报告 + 预警（severity≥high，去重生效） |
| AC-03 | 某节点异常走降级、errors 非空但整图不崩 |
| AC-04 | 无 placeholder；持久化仅在 persist_result |
| AC-05 | 更新 `task_m6/STATUS.md` 本行 |
