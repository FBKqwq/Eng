# M4-03：图状态 analysis/state

## Agent 角色

状态契约 Agent — 完善 `create_initial_state` 与 node_trace 追加辅助。

## 唯一负责文件

```
app/services/analysis/state.py
```

## 禁止修改

- `schemas.py`、`graph_*.py`、其他 analysis 文件

## 前置依赖

- M3 完成

## 开发要求

### 1. `create_initial_state(trigger_type, **kwargs) -> AnalysisState`
- 生成 `task_id`（缺省 uuid4）
- 初始化 `node_trace=[]`、`errors=[]`、`metrics={}`、`raw_logs=[]` 等空容器
- 合并 `time_window`、`trigger_event` 等传入字段

### 2. `append_node_trace(state, node_name, status, *, duration_ms=None, output_summary=None, error_message=None) -> None`
- 向 `state["node_trace"]` 追加一条记录（结构对齐 `schemas.NodeTraceEntry`）

### 3. `record_error(state, node_name, message) -> None`
- 向 `state["errors"]` 追加节点级错误，供降级路径使用

### 4. 约定
- 纯状态操作，不调用 ES/LLM
- 无 placeholder

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `create_initial_state` 生成非空 task_id 与初始化容器 |
| AC-02 | `append_node_trace` 正确追加记录 |
| AC-03 | `record_error` 正确追加错误 |
| AC-04 | 更新 `task_m4/STATUS.md` 本行 |
