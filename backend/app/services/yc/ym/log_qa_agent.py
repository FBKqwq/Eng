"""AI日志问答助手

基于大语言模型的日志智能问答服务，支持：
1. 自然语言查询日志
2. 日志摘要生成
3. 异常模式识别
4. 问题诊断建议
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

# 模拟日志数据存储
SIMULATED_LOGS = [
    {"timestamp": "2026-06-24T10:00:00Z", "level": "ERROR", "service": "order-service", "message": "数据库连接超时，无法处理订单请求"},
    {"timestamp": "2026-06-24T10:00:05Z", "level": "WARN", "service": "payment-service", "message": "支付网关响应延迟超过3秒"},
    {"timestamp": "2026-06-24T10:00:10Z", "level": "INFO", "service": "user-service", "message": "用户登录成功，ID: 12345"},
    {"timestamp": "2026-06-24T10:00:15Z", "level": "ERROR", "service": "order-service", "message": "订单创建失败，库存不足"},
    {"timestamp": "2026-06-24T10:00:20Z", "level": "WARN", "service": "inventory-service", "message": "库存预警，商品ID: 67890 库存不足100件"},
    {"timestamp": "2026-06-24T10:00:25Z", "level": "INFO", "service": "shipping-service", "message": "订单发货成功，订单号: ORDER-20260624001"},
    {"timestamp": "2026-06-24T10:00:30Z", "level": "ERROR", "service": "payment-service", "message": "支付失败，金额超限"},
    {"timestamp": "2026-06-24T10:00:35Z", "level": "DEBUG", "service": "api-gateway", "message": "请求路由完成，耗时: 150ms"},
    {"timestamp": "2026-06-24T10:00:40Z", "level": "ERROR", "service": "order-service", "message": "数据库连接池耗尽，无法获取连接"},
    {"timestamp": "2026-06-24T10:00:45Z", "level": "INFO", "service": "notification-service", "message": "短信通知发送成功，手机号: 138****8888"},
]

# 问答模板
QA_TEMPLATES = {
    "error_query": {
        "patterns": ["错误", "异常", "失败", "error", "exception", "failed"],
        "response": "根据日志分析，检测到以下错误：\n{error_logs}\n\n建议：{suggestion}"
    },
    "service_query": {
        "patterns": ["服务", "service", "订单", "支付", "库存", "用户"],
        "response": "{service}服务相关日志：\n{logs}\n\n服务状态：{status}"
    },
    "time_query": {
        "patterns": ["时间", "今天", "最近", "过去", "today", "recent", "last"],
        "response": "{time_range}内的日志摘要：\n{summary}"
    },
    "summary": {
        "patterns": ["摘要", "总结", "概览", "summary", "overview"],
        "response": "日志分析摘要：\n\n📊 日志统计：\n{stats}\n\n⚠️ 异常发现：\n{anomalies}\n\n💡 建议：\n{suggestions}"
    },
    "trend": {
        "patterns": ["趋势", "变化", "趋势分析", "trend", "pattern"],
        "response": "趋势分析结果：\n\n📈 变化趋势：\n{trend}\n\n🔍 关键发现：\n{findings}"
    }
}


class QAAnswer:
    """问答结果"""
    def __init__(self):
        self.answer_id = str(uuid4())
        self.question = ""
        self.answer = ""
        self.confidence = 0.0
        self.sources: List[Dict] = []
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.type = "general"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer_id": self.answer_id,
            "question": self.question,
            "answer": self.answer,
            "confidence": self.confidence,
            "sources": self.sources,
            "timestamp": self.timestamp,
            "type": self.type
        }


def analyze_question(question: str) -> str:
    """分析问题类型"""
    for qtype, template in QA_TEMPLATES.items():
        for pattern in template["patterns"]:
            if pattern in question:
                return qtype
    return "general"


def query_logs(question: str, filters: Optional[Dict] = None) -> List[Dict]:
    """根据问题查询日志"""
    logs = SIMULATED_LOGS.copy()
    
    # 根据问题动态过滤
    if "错误" in question or "error" in question.lower():
        logs = [l for l in logs if l["level"] == "ERROR"]
    if "警告" in question or "warn" in question.lower():
        logs = [l for l in logs if l["level"] in ["ERROR", "WARN"]]
    if "订单" in question:
        logs = [l for l in logs if l["service"] == "order-service"]
    if "支付" in question:
        logs = [l for l in logs if l["service"] == "payment-service"]
    if "库存" in question:
        logs = [l for l in logs if l["service"] == "inventory-service"]
    
    return logs[:10]


def generate_answer(question: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """生成AI回答"""
    result = QAAnswer()
    result.question = question
    
    try:
        question_type = analyze_question(question)
        result.type = question_type
        
        if question_type == "error_query":
            answer, confidence, sources = generate_error_answer(question)
        elif question_type == "service_query":
            answer, confidence, sources = generate_service_answer(question)
        elif question_type == "time_query":
            answer, confidence, sources = generate_time_answer(question)
        elif question_type == "summary":
            answer, confidence, sources = generate_summary_answer(question)
        elif question_type == "trend":
            answer, confidence, sources = generate_trend_answer(question)
        else:
            answer, confidence, sources = generate_general_answer(question)
        
        result.answer = answer
        result.confidence = confidence
        result.sources = sources
        
    except Exception as e:
        result.answer = f"抱歉，我无法回答这个问题。错误信息：{str(e)}"
        result.confidence = 0.0
    
    return result.to_dict()


def generate_error_answer(question: str) -> tuple:
    """生成错误查询回答"""
    error_logs = query_logs(question)
    
    if not error_logs:
        return "未找到相关错误日志。", 0.8, []
    
    error_list = "\n".join([f"- [{log['timestamp']}] [{log['service']}] {log['message']}" for log in error_logs])
    
    services_with_errors = set(log["service"] for log in error_logs)
    suggestions = []
    if "order-service" in services_with_errors:
        suggestions.append("检查订单服务的数据库连接配置")
    if "payment-service" in services_with_errors:
        suggestions.append("检查支付网关的网络连接")
    if len(error_logs) > 3:
        suggestions.append("系统可能存在系统性问题，建议进行全面检查")
    
    suggestion_text = "\n".join([f"{i+1}. {s}" for i, s in enumerate(suggestions)])
    
    answer = f"""根据日志分析，检测到以下错误：

{error_list}

建议：
{suggestion_text}"""
    
    return answer, 0.85, error_logs[:5]


def generate_service_answer(question: str) -> tuple:
    """生成服务查询回答"""
    service_name = "未知服务"
    if "订单" in question:
        service_name = "订单服务"
    elif "支付" in question:
        service_name = "支付服务"
    elif "库存" in question:
        service_name = "库存服务"
    elif "用户" in question:
        service_name = "用户服务"
    
    logs = query_logs(question)
    
    if not logs:
        return f"未找到{service_name}相关的日志。", 0.75, []
    
    log_list = "\n".join([f"- [{log['timestamp']}] [{log['level']}] {log['message']}" for log in logs])
    
    error_count = sum(1 for l in logs if l["level"] == "ERROR")
    warn_count = sum(1 for l in logs if l["level"] == "WARN")
    
    status = "🟢 正常"
    if error_count > 2:
        status = "🔴 异常"
    elif warn_count > 0:
        status = "🟡 警告"
    
    answer = f"""{service_name}相关日志：

{log_list}

服务状态：{status}
- 错误数量：{error_count}
- 警告数量：{warn_count}"""
    
    return answer, 0.8, logs[:5]


def generate_time_answer(question: str) -> tuple:
    """生成时间范围查询回答"""
    time_range = "最近1小时"
    
    logs = query_logs(question)
    error_count = sum(1 for l in logs if l["level"] == "ERROR")
    warn_count = sum(1 for l in logs if l["level"] == "WARN")
    info_count = sum(1 for l in logs if l["level"] == "INFO")
    
    summary = f"""📊 日志统计：
- 总日志数：{len(logs)}
- 错误：{error_count}
- 警告：{warn_count}
- 信息：{info_count}

📝 最近日志：
{chr(10).join([f"- [{log['timestamp']}] [{log['service']}] {log['message']}" for log in logs[:5]])}"""
    
    answer = f"""{time_range}内的日志摘要：

{summary}"""
    
    return answer, 0.85, logs[:5]


def generate_summary_answer(question: str) -> tuple:
    """生成摘要回答"""
    logs = SIMULATED_LOGS
    
    stats = f"""• 总日志数：{len(logs)}
• 错误日志：{sum(1 for l in logs if l['level'] == 'ERROR')}
• 警告日志：{sum(1 for l in logs if l['level'] == 'WARN')}
• 信息日志：{sum(1 for l in logs if l['level'] == 'INFO')}
• 调试日志：{sum(1 for l in logs if l['level'] == 'DEBUG')}"""
    
    error_logs = [l for l in logs if l['level'] == 'ERROR']
    anomalies = "\n".join([f"• [{l['service']}] {l['message']}" for l in error_logs]) if error_logs else "无明显异常"
    
    suggestions = """1. 建议关注order-service的数据库连接问题
2. 检查payment-service的支付网关状态
3. 考虑增加数据库连接池大小"""
    
    answer = f"""日志分析摘要：

📊 日志统计：
{stats}

⚠️ 异常发现：
{anomalies}

💡 建议：
{suggestions}"""
    
    return answer, 0.9, logs[:5]


def generate_trend_answer(question: str) -> tuple:
    """生成趋势分析回答"""
    logs = SIMULATED_LOGS
    
    error_count = sum(1 for l in logs if l['level'] == 'ERROR')
    trend = f"""• 错误率趋势：{'上升' if error_count > 3 else '稳定'}
• 服务异常：order-service出现多次数据库连接问题
• 支付服务：存在响应延迟问题"""
    
    findings = """1. 数据库连接池可能需要扩容
2. 支付网关响应时间超过阈值
3. 库存服务存在预警"""
    
    answer = f"""趋势分析结果：

📈 变化趋势：
{trend}

🔍 关键发现：
{findings}"""
    
    return answer, 0.85, logs[:5]


def generate_general_answer(question: str) -> tuple:
    """生成通用回答"""
    logs = query_logs(question)
    
    if logs:
        log_summary = "\n".join([f"- [{log['timestamp']}] [{log['service']}] [{log['level']}] {log['message']}" for log in logs[:5]])
        answer = f"""根据您的查询，找到以下相关日志：

{log_summary}

如需更详细的分析，请提供更具体的问题，例如：
• "最近有哪些错误？"
• "订单服务的状态如何？"
• "帮我总结今天的日志"
• "分析一下系统趋势"""
    else:
        answer = f"""您好！我是AI日志问答助手。

我可以帮您：
• 查询特定服务的日志
• 分析错误和异常
• 生成日志摘要
• 识别趋势和模式

请问您想查询什么？"""
    
    return answer, 0.75, logs[:5]


def get_conversation_history(limit: int = 10) -> List[Dict]:
    """获取对话历史"""
    return []
