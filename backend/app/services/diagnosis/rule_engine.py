"""规则分流引擎。

当前：classify_by_rules 为关键词硬编码分流（兼容现有诊断 API）。
match_log 读取 rule_definitions 声明式规则表，输出 trigger_subgraph 标记。
详见：doc/后端开发总体规划-Services-LangGraph-MCP.md §1.3
"""

from __future__ import annotations

from typing import Any, Callable

from app.services.diagnosis.rule_definitions import get_rule_definitions

_OPERATORS: dict[str, Callable[[float, float], bool]] = {
    ">=": lambda actual, expected: actual >= expected,
    ">": lambda actual, expected: actual > expected,
    "<=": lambda actual, expected: actual <= expected,
    "<": lambda actual, expected: actual < expected,
    "==": lambda actual, expected: actual == expected,
    "!=": lambda actual, expected: actual != expected,
}


def _to_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _unmatched_result(log_event: dict) -> dict:
    return {
        "ok": True,
        "matched": False,
        "rule_id": None,
        "rule_name": None,
        "severity": None,
        "trigger_subgraph": False,
        "log_event_id": log_event.get("log_id"),
    }


def _matched_result(rule: dict[str, Any], log_event: dict) -> dict:
    return {
        "ok": True,
        "matched": True,
        "rule_id": rule["rule_id"],
        "rule_name": rule["rule_name"],
        "severity": rule["severity"],
        "trigger_subgraph": bool(rule.get("trigger_subgraph", False)),
        "log_event_id": log_event.get("log_id"),
    }


def _match_error_code(match_spec: dict[str, Any], log_event: dict) -> bool:
    expected = match_spec.get("error_code")
    if expected is None:
        return False
    return log_event.get("error_code") == expected


def _match_threshold(match_spec: dict[str, Any], log_event: dict) -> bool:
    field = match_spec.get("field")
    operator = match_spec.get("operator")
    threshold = match_spec.get("value")
    if not field or not operator or threshold is None:
        return False
    compare_fn = _OPERATORS.get(str(operator))
    if compare_fn is None:
        return False
    actual = _to_number(log_event.get(field))
    expected = _to_number(threshold)
    if actual is None or expected is None:
        return False
    return compare_fn(actual, expected)


def _match_frequency(_match_spec: dict[str, Any], _log_event: dict) -> bool:
    """频率规则需 aggregation 计数，单条日志无法判定命中。"""
    return False


def _rule_matches(rule: dict[str, Any], log_event: dict) -> bool:
    kind = rule.get("kind")
    match_spec = rule.get("match") or {}
    if kind == "error_code":
        return _match_error_code(match_spec, log_event)
    if kind == "threshold":
        return _match_threshold(match_spec, log_event)
    if kind == "frequency":
        return _match_frequency(match_spec, log_event)
    return False


def match_log(log_event: dict) -> dict:
    """对单条日志事件执行声明式规则匹配。"""
    event = log_event if isinstance(log_event, dict) else {}
    for rule in get_rule_definitions():
        if _rule_matches(rule, event):
            return _matched_result(rule, event)
    return _unmatched_result(event)


def classify_by_rules(keyword: str | None) -> dict:
    keyword = (keyword or "").lower()
    if any(token in keyword for token in ("timeout", "超时", "slow", "latency")):
        return {"route": "rule", "anomaly_type": "接口超时", "severity": "high"}
    if any(token in keyword for token in ("pay", "payment", "支付", "pay_fail")):
        return {"route": "rule", "anomaly_type": "支付异常", "severity": "high"}
    if any(token in keyword for token in ("db_timeout", "database", "mysql", "数据库")):
        return {"route": "rule", "anomaly_type": "数据库异常", "severity": "high"}
    if any(token in keyword for token in ("stock", "inventory", "库存")):
        return {"route": "rule", "anomaly_type": "库存异常", "severity": "medium"}
    return {"route": "llm_pending", "anomaly_type": "未知异常", "severity": "medium"}
