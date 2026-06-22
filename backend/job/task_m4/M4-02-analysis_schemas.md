# M4-02：触发标准化 analysis/schemas

## Agent 角色

触发标准化 Agent — 实现 `normalize_trigger`，统一定时/规则两类触发输入。

## 唯一负责文件

```
app/services/analysis/schemas.py
```

## 禁止修改

- `state.py`、`graph_*.py`、其他 analysis 文件

## 前置依赖

- M3 完成

## 开发要求

### 1. 保留并复用现有模型
`TriggerEvent`、`NodeTraceEntry`、`TriggerType`、`NodeRunStatus` 已定义，按需完善。

### 2. `normalize_trigger(raw: dict) -> dict`
- 解析 `trigger_type`（`scheduled` | `rule`），缺失/非法 → `{"ok": False, "error": "invalid trigger_type"}`
- 定时触发：补全 `time_window`（缺省用 `now - schedule_minutes` ~ `now`，可从 config 读取窗口长度）
- 规则触发：保留 `trigger_event` 原始日志
- 返回 `{"ok": True, "trigger": TriggerEvent(...).model_dump()}`，**无 placeholder**

### 3. node_trace 辅助（可选，便于子图复用）
- 提供 `make_node_trace(node_name, status, ...) -> dict`（基于 `NodeTraceEntry`）

### 4. 约定
- 不抛裸异常；非法输入结构化返回

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | 合法 scheduled/rule 触发 → ok=True 且含标准 TriggerEvent |
| AC-02 | 非法 trigger_type → ok=False，不抛异常 |
| AC-03 | 无 placeholder 键 |
| AC-04 | 更新 `task_m4/STATUS.md` 本行 |
