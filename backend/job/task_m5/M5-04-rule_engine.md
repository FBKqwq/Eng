# M5-04：规则匹配 rule_engine

## Agent 角色

规则引擎 Agent — 将 `match_log` 从占位升级为读取 `rule_definitions` 的声明式匹配。

## 唯一负责文件

```
app/services/diagnosis/rule_engine.py
```

## 禁止修改

- `rule_definitions.py`（只 import `get_rule_definitions`）
- `analyzer.py`、`tools/rule_tools.py`（M2 已薄包装，自动透传）

## 前置依赖

- M5-03 为 `已完成`/`已合并`

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.diagnosis.rule_definitions import get_rule_definitions; assert any(r['match'].get('error_code')=='PAY_FAIL' for r in get_rule_definitions())"
```

## 开发要求

### 1. `match_log(log_event: dict) -> dict`
- 遍历 `get_rule_definitions()`，按 `kind` 匹配：
  - `error_code`：比对 `log_event.error_code`
  - `threshold`：比对数值字段（status_code/response_time_ms/request_time）
  - `frequency`：第一版可标注「需 aggregation 计数，单条匹配返回 matched=False 并注明」
- 命中：返回 `{"ok": True, "matched": True, "rule_id", "rule_name", "severity", "trigger_subgraph", "log_event_id"}`
- 未命中：`{"ok": True, "matched": False, "trigger_subgraph": False, ...}`
- **去除 placeholder**；不抛裸异常

### 2. 保留 `classify_by_rules`
- 现有关键词分流函数保持兼容（诊断 API 仍在用），不破坏

### 3. 约定
- 纯规则匹配，不调用 ES/LLM
- 输出结构供 `trigger_scanner` 与 M2 工具 `rule_match_log` 复用

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `match_log` 对 PAY_FAIL 日志返回 matched=True、trigger_subgraph=True |
| AC-02 | 未命中返回 matched=False，无 placeholder |
| AC-03 | `classify_by_rules` 行为不变 |
| AC-04 | 更新 `task_m5/STATUS.md` 本行 |
