# M7-04：定时子图接入 analyze_relations 节点

## Agent 角色

定时子图 Agent — 在 `build_evidence` 与 `generate_report` 之间插入 `analyze_relations` 节点，并把 relations 注入周期报告。

## 唯一负责文件

```
app/services/analysis/graph_scheduled.py
```

## 禁止修改

- relation_chain / report_chain / evidence_builder / state / schemas（只 import）
- graph_main / scheduler / graph_rule

## 前置依赖

- M7-03（relation_chain.discover_relations）为 `已完成`/`已合并`

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.langchain.relation_chain import discover_relations; print('deps ok')"
```

## 详细任务内容

当前定时子图节点流（六节点）：
```text
build_time_window → plan_queries → aggregate_metrics → sample_logs → build_evidence → generate_report → END
```

目标节点流（§2.4，七节点）：
```text
build_time_window → plan_queries → aggregate_metrics → sample_logs
  → build_evidence → analyze_relations → generate_report → END
```

### 1. 新增节点 `_node_analyze_relations`
- 读取 state 中的 evidence package；调用 `relation_chain.discover_relations(evidence_package)`；
- 将 `relations` 写入 state（新增 state 字段或复用既有容器，参照现有 `_pack` / `append_node_trace` 写法）；
- 记录 `node_trace`（节点名、状态 success/skipped/failed、耗时）；
- **降级**：`discover_relations` 返回 `degraded=True` 或 relations 为空时，记 `skipped`，**不阻断**后续 `generate_report`。

### 2. 注册节点与边
- `_NODE_SEQUENCE` / `add_node` / `add_edge`：在 `build_evidence` 后、`generate_report` 前插入 `analyze_relations`。

### 3. relations 注入报告
- 在 `_node_generate_report` 中把 relations 作为附加上下文：
  - 优先把 relations 并入证据上下文供 report_chain 参考；
  - 若 report_chain 签名不便扩展，则在报告 dict 产出后追加 `report["relations"] = relations`（保证报告对象携带关系发现结果，供前端/持久化展示）。
- **向后兼容**：relations 为空时，报告内容与 M4 等价（不得改变既有字段语义）。

### 约定
- 节点失败写 `state["errors"]` 并降级；无 placeholder。
- 不要 commit。

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | 子图节点流含 7 节点，`analyze_relations` 位于 build_evidence 与 generate_report 之间 |
| AC-02 | relations 非空（mock）时写入报告；node_trace 含 analyze_relations 记录 |
| AC-03 | LLM/关系发现不可用时该节点 skipped，报告仍正常产出（与 M4 等价） |
| AC-04 | M4/M6 既有测试回归通过（由 M7-09 验证；本任务须自测子图 invoke 不报错） |
| AC-05 | 更新 `task_m7/STATUS.md` 中 M7-04 行 |
