def classify_by_rules(keyword: str | None) -> dict:
    keyword = (keyword or "").lower()
    if "timeout" in keyword:
        return {"route": "rule", "anomaly_type": "接口超时", "severity": "high"}
    if "pay" in keyword:
        return {"route": "rule", "anomaly_type": "支付异常", "severity": "high"}
    return {"route": "llm", "anomaly_type": "未知异常", "severity": "medium"}
