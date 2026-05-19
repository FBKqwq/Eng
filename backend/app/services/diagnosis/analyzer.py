from app.schemas.diagnosis import DiagnosisRequest
from app.services.elasticsearch.log_query_service import search_recent_context
from app.services.diagnosis.rule_engine import classify_by_rules


def analyze_logs(payload: DiagnosisRequest) -> dict:
    rule_text = _diagnosis_rule_text(payload)
    rule_result = classify_by_rules(rule_text)
    context = _fetch_context(payload)
    evidence_logs = context.get("items", []) if payload.include_context_logs else []
    context_available = bool(context.get("available")) if payload.include_context_logs else False

    return {
        "message": "规则诊断已完成；LangChain/LangGraph 深度分析仍待接入",
        "input": payload.model_dump(),
        "diagnosis": {
            "anomaly_type": rule_result["anomaly_type"],
            "severity": rule_result["severity"],
            "route": rule_result["route"],
            "root_cause": _root_cause(rule_result, evidence_logs, context_available),
            "suggestion": [
                "检查 Kafka 到 Logstash 链路是否正常",
                "检查 Elasticsearch 索引是否持续写入",
                "检查对应服务最近 5 分钟错误日志",
            ],
            "evidence_logs": evidence_logs,
            "context_summary": {
                "available": context_available,
                "total": context.get("total", 0),
                "used_logs": len(evidence_logs),
                "error": context.get("error"),
            },
        },
    }


def _diagnosis_rule_text(payload: DiagnosisRequest) -> str:
    preferred = " ".join(t.value for t in (payload.preferred_anomaly_types or []))
    return " ".join(
        part
        for part in [
            payload.keyword,
            payload.error_code,
            payload.service_name,
            payload.trace_id,
            preferred,
            payload.remark,
        ]
        if part
    )


def _fetch_context(payload: DiagnosisRequest) -> dict:
    if not payload.include_context_logs:
        return {"available": False, "items": [], "total": 0, "error": None}
    return search_recent_context(
        trace_id=payload.trace_id,
        service_name=payload.service_name,
        error_code=payload.error_code,
        limit=payload.max_logs,
    )


def _root_cause(rule_result: dict, evidence_logs: list[dict], context_available: bool) -> str:
    if evidence_logs:
        return f"规则识别为{rule_result['anomaly_type']}，已拉取到 {len(evidence_logs)} 条相关日志作为诊断证据"
    if context_available:
        return f"规则识别为{rule_result['anomaly_type']}，但当前筛选条件下未检索到相关日志"
    return f"规则识别为{rule_result['anomaly_type']}，日志上下文暂不可用或未配置"
