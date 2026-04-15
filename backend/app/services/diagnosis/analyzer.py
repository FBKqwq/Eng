from app.schemas.diagnosis import DiagnosisRequest
from app.services.diagnosis.rule_engine import classify_by_rules


def analyze_logs(payload: DiagnosisRequest) -> dict:
    rule_result = classify_by_rules(payload.keyword)
    return {
        "message": "这是智能诊断占位实现，后续可接 LangChain/LangGraph",
        "input": payload.model_dump(),
        "diagnosis": {
            "anomaly_type": rule_result["anomaly_type"],
            "severity": rule_result["severity"],
            "route": rule_result["route"],
            "root_cause": "待接入日志检索与图式诊断流程",
            "suggestion": [
                "检查 Kafka 到 Logstash 链路是否正常",
                "检查 Elasticsearch 索引是否持续写入",
                "检查对应服务最近 5 分钟错误日志",
            ],
        },
    }
