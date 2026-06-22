# M5-03：声明式规则表 rule_definitions

## Agent 角色

规则声明 Agent — 填充三类规则的声明式表，供 rule_engine 读取。

## 唯一负责文件

```
app/services/diagnosis/rule_definitions.py
```

## 禁止修改

- `rule_engine.py`（由 M5-04 读取本表）
- 其他文件

## 前置依赖

- M1 完成

## 开发要求

### 1. 填充 `RULE_DEFINITIONS`（三类）
- **错误码规则**：`PAY_FAIL`、`DB_TIMEOUT`、`CIRCUIT_OPEN`、`UNAVAILABLE` 等 → `trigger_subgraph=True`
- **阈值规则**：`status_code >= 500`、`response_time_ms > 3000`、`request_time > 3`
- **频率规则**：同服务 N 分钟内 ERROR ≥ M（声明结构即可，频率计算依赖 aggregation，匹配实现可在 M5-04 标注）

每条结构（与 §1.3 对齐）：
```python
{
  "rule_id": "R_PAY_FAIL",
  "rule_name": "支付失败",
  "kind": "error_code",          # threshold | error_code | frequency
  "match": {"error_code": "PAY_FAIL"},
  "severity": "high",            # low|medium|high|critical
  "trigger_subgraph": True,
}
```

### 2. `get_rule_definitions() -> list[dict]`
- 返回当前生效规则列表（保持函数签名）

### 3. 约定
- 纯数据声明，不调用 ES/LLM
- `PAY_FAIL` 必须存在且 `trigger_subgraph=True`（M5 验收依赖）
- 去除「占位」字样

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | RULE_DEFINITIONS 非空，含三类规则 |
| AC-02 | 含 `error_code=PAY_FAIL` 且 `trigger_subgraph=True` |
| AC-03 | `get_rule_definitions` 返回完整列表 |
| AC-04 | 更新 `task_m5/STATUS.md` 本行 |
