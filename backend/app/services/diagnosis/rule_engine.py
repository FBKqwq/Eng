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
