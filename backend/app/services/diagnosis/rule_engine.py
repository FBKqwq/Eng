"""规则分流引擎。

当前：classify_by_rules 为关键词硬编码分流（兼容现有诊断 API）。
规划：读取 rule_definitions 声明式规则表，输出 trigger_subgraph 标记。
详见：doc/后端开发总体规划-Services-LangGraph-MCP.md §1.3
"""


def match_log(log_event: dict) -> dict:
    """对单条日志事件执行规则匹配（占位，供 MCP rule_match_log 与规则子图使用）。"""
    return {
        "ok": False,
        "placeholder": True,
        "message": "match_log 尚未实现，待 P1 接入 rule_definitions",
        "rule_id": None,
        "rule_name": None,
        "matched": False,
        "severity": None,
        "trigger_subgraph": False,
        "log_event_id": log_event.get("log_id"),
    }


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
