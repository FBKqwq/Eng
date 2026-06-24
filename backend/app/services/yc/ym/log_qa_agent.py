"""AI日志问答助手 - 智能对话版

基于大语言模型的日志智能问答服务，支持：
1. 自然语言查询日志 - 理解多样化的提问方式
2. 日志自动摘要生成 - 动态生成摘要内容
3. 异常模式智能识别 - 智能检测异常
4. 问题诊断与修复建议 - 基于知识库的智能建议
5. 根因分析增强 - 深入分析问题根源
6. 日志趋势预测 - 预测未来趋势
7. 智能日志分类 - 自动分类日志
8. 上下文感知对话 - 记住对话历史
9. 自然语言对话 - 支持多轮对话
10. DeepSeek LLM 集成 - 支持大模型增强
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_TIMEOUT = int(os.getenv("DEEPSEEK_TIMEOUT", "30"))

# 当前使用的模型
CURRENT_MODEL = "deepseek" if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY != "your_deepseek_api_key_here" else "local"

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

# 问答模板 - 扩展版
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
    },
    "classify": {
        "patterns": ["分类", "类型", "类别", "classify", "category"],
        "response": "日志分类结果：\n\n📋 分类统计：\n{classification}\n\n🔍 各类别详情：\n{details}"
    },
    "root_cause": {
        "patterns": ["根因", "原因", "为什么", "why", "root cause"],
        "response": "根因分析结果：\n\n🎯 主要原因：\n{primary_cause}\n\n🔗 关联因素：\n{factors}\n\n💡 修复建议：\n{solutions}"
    },
    "predict": {
        "patterns": ["预测", "未来", "将会", "predict", "forecast"],
        "response": "趋势预测结果：\n\n📈 预测趋势：\n{prediction}\n\n⚠️ 潜在风险：\n{risks}\n\n🛡️ 建议措施：\n{measures}"
    },
    "suggest": {
        "patterns": ["建议", "修复", "解决", "suggest", "fix", "solve"],
        "response": "智能修复建议：\n\n💡 问题分析：\n{analysis}\n\n📝 修复方案：\n{solutions}\n\n✅ 操作步骤：\n{steps}"
    }
}

# 日志分类规则
LOG_CATEGORIES = {
    "数据库": ["数据库", "db", "mysql", "postgres", "connection", "query", "sql"],
    "网络": ["网络", "network", "http", "tcp", "connection", "timeout", "gateway"],
    "认证": ["认证", "auth", "login", "token", "session", "权限"],
    "性能": ["性能", "performance", "timeout", "delay", "slow", "latency"],
    "业务": ["订单", "支付", "库存", "用户", "order", "payment", "inventory"],
    "系统": ["系统", "system", "server", "memory", "cpu", "disk"]
}

# 对话历史存储（模拟）
CONVERSATION_HISTORY = []

# 回答模板变化 - 增加多样化表达
ANSWER_TEMPLATES = {
    "greetings": [
        "您好！我是AI日志助手，随时为您服务！",
        "你好呀！有什么我可以帮助您的吗？",
        "嗨！很高兴为您服务，请问需要什么帮助？",
        "您好！请问我可以帮您查询什么日志信息？"
    ],
    "thanks": [
        "不客气！有任何问题随时来找我。",
        "很高兴能帮到您！",
        "不用谢，这是我应该做的。",
        "随时为您效劳！"
    ],
    "error_intro": [
        "根据日志分析，我发现了一些问题：",
        "让我看看日志...发现以下错误：",
        "分析完成，检测到以下异常：",
        "查看日志后，我发现了几个需要关注的问题："
    ],
    "summary_intro": [
        "让我为您总结一下：",
        "好的，这是当前的日志概况：",
        "根据分析，为您整理如下：",
        "这是目前的情况总结："
    ],
    "suggestion_intro": [
        "基于分析，我有以下建议：",
        "针对这些问题，建议采取以下措施：",
        "为了解决这些问题，您可以：",
        "根据我的分析，这里有一些建议："
    ],
    "no_results": [
        "暂时没有找到相关日志。",
        "没有发现匹配的日志信息。",
        "未检索到相关内容。",
        "抱歉，没有找到符合条件的日志。"
    ]
}

# 语气词增强
TONE_WORDS = {
    "positive": ["太棒了", "太好了", "非常好", "不错"],
    "neutral": ["好的", "了解", "明白", "知道了"],
    "concerned": ["需要关注", "值得注意", "建议留意", "提醒一下"]
}

# 常见问题与解决方案知识库
KNOWLEDGE_BASE = {
    "数据库连接超时": {
        "cause": "数据库连接池耗尽或数据库服务不可用",
        "solutions": ["增加连接池大小", "检查数据库服务状态", "优化慢查询", "考虑读写分离"],
        "steps": ["1. 检查数据库服务是否正常运行", "2. 查看连接池配置", "3. 分析慢查询日志", "4. 考虑扩容或优化"]
    },
    "支付网关响应延迟": {
        "cause": "第三方支付网关响应慢或网络问题",
        "solutions": ["检查网络连接", "切换备用网关", "增加超时时间", "实现熔断机制"],
        "steps": ["1. 检查网络连通性", "2. 联系支付服务商", "3. 启用备用通道", "4. 实施降级方案"]
    },
    "库存不足": {
        "cause": "库存管理系统数据不一致或库存耗尽",
        "solutions": ["同步库存数据", "设置库存预警", "补货", "限制超卖"],
        "steps": ["1. 检查库存数据一致性", "2. 补充库存", "3. 调整预警阈值", "4. 优化库存管理流程"]
    },
    "连接池耗尽": {
        "cause": "连接池配置过小或连接未正确释放",
        "solutions": ["增加连接池大小", "检查连接泄漏", "设置连接超时", "优化连接使用"],
        "steps": ["1. 检查连接池配置参数", "2. 查找连接泄漏代码", "3. 设置合理超时时间", "4. 优化连接复用"]
    }
}


import random

def random_choice(items: list) -> any:
    """随机选择列表中的一个元素"""
    return random.choice(items)

def format_log_message(log: dict) -> str:
    """格式化日志消息，使其更易读"""
    return f"[{log['timestamp'].replace('T', ' ').replace('Z', '')}] [{log['service']}] [{log['level']}] {log['message']}"

def get_conversation_context(last_n: int = 3) -> str:
    """获取对话上下文"""
    if len(CONVERSATION_HISTORY) == 0:
        return ""
    
    recent = CONVERSATION_HISTORY[-last_n:]
    context = "\n".join([f"用户: {item['question']}\n助手: {item['answer'][:100]}..." for item in recent])
    return context

def add_conversation(question: str, answer: str):
    """添加对话到历史记录"""
    CONVERSATION_HISTORY.append({
        "question": question,
        "answer": answer,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    # 保持历史记录在合理范围内
    if len(CONVERSATION_HISTORY) > 50:
        CONVERSATION_HISTORY.pop(0)

def is_greeting(question: str) -> bool:
    """检测是否为问候语"""
    # 移除首尾空格
    q = question.strip()
    
    # 中文问候语（不需要lower，因为中文没有大小写）
    greetings_cn = ["你好", "您好", "嗨", "你好！", "您好！", "您好吗", "最近好吗"]
    # 英文问候语
    greetings_en = ["hello", "hi", "hello!", "hi!"]
    
    # 检查中文问候语（保持原样）
    for greeting in greetings_cn:
        if q == greeting or q.startswith(greeting):
            return True
    
    # 检查英文问候语（转换为小写）
    q_lower = q.lower()
    for greeting in greetings_en:
        if q_lower == greeting or q_lower.startswith(greeting):
            return True
    
    return False

def is_thanks(question: str) -> bool:
    """检测是否为感谢语"""
    # 移除首尾空格
    q = question.strip()
    
    # 中文感谢语
    thanks_cn = ["谢谢", "谢谢你", "感谢", "谢谢！", "非常感谢"]
    # 英文感谢语
    thanks_en = ["thank", "thanks", "thank you", "thanks!"]
    
    # 检查中文感谢语
    for thank in thanks_cn:
        if q == thank or q.startswith(thank):
            return True
    
    # 检查英文感谢语
    q_lower = q.lower()
    for thank in thanks_en:
        if q_lower == thank or q_lower.startswith(thank):
            return True
    
    return False

def analyze_question_intent(question: str) -> tuple:
    """分析问题意图，返回意图类型和关键词"""
    intent_keywords = {
        "greeting": ["你好", "您好", "嗨", "hello", "hi"],
        "thanks": ["谢谢", "感谢", "thank"],
        "error": ["错误", "异常", "失败", "error", "exception", "failed", "崩溃"],
        "service": ["服务", "状态", "运行", "service", "订单", "支付", "库存"],
        "summary": ["摘要", "总结", "概览", "summary", "overview", "情况"],
        "trend": ["趋势", "变化", "预测", "trend", "pattern", "未来"],
        "classify": ["分类", "类型", "类别", "classify", "category"],
        "root_cause": ["原因", "为什么", "根因", "why", "cause"],
        "suggest": ["建议", "修复", "解决", "suggest", "fix", "solve"],
        "query": ["查询", "查一下", "看看", "find", "search"]
    }
    
    question_lower = question.lower()
    
    for intent, keywords in intent_keywords.items():
        for keyword in keywords:
            if keyword.lower() in question_lower:
                return intent, keyword
    
    return "general", None

def generate_natural_answer(question: str, logs: list) -> tuple:
    """生成更自然的回答"""
    intent, keyword = analyze_question_intent(question)
    
    # 检测问候语
    if is_greeting(question):
        return random_choice(ANSWER_TEMPLATES["greetings"]), 0.95, []
    
    # 检测感谢语
    if is_thanks(question):
        return random_choice(ANSWER_TEMPLATES["thanks"]), 0.95, []
    
    # 基于意图生成回答
    if intent == "error":
        return generate_natural_error_answer(question, logs)
    elif intent == "service":
        return generate_natural_service_answer(question, logs)
    elif intent == "summary":
        return generate_natural_summary_answer(question, logs)
    elif intent == "trend":
        return generate_natural_trend_answer(question, logs)
    elif intent == "classify":
        return generate_natural_classify_answer(question, logs)
    elif intent == "root_cause":
        return generate_natural_root_cause_answer(question, logs)
    elif intent == "suggest":
        return generate_natural_suggest_answer(question, logs)
    else:
        return generate_natural_general_answer(question, logs)


def generate_natural_error_answer(question: str, logs: list) -> tuple:
    """生成自然的错误查询回答"""
    error_logs = [l for l in logs if l["level"] == "ERROR"]
    
    if not error_logs:
        return f"{random_choice(ANSWER_TEMPLATES['no_results'])} 当前系统运行正常。", 0.85, []
    
    intro = random_choice(ANSWER_TEMPLATES["error_intro"])
    log_list = "\n".join([f"- {format_log_message(log)}" for log in error_logs[:5]])
    
    # 动态生成建议
    services_with_errors = set(log["service"] for log in error_logs)
    suggestions = []
    
    if "order-service" in services_with_errors:
        suggestions.append("检查订单服务的数据库连接配置")
    if "payment-service" in services_with_errors:
        suggestions.append("检查支付网关的网络连接")
    if len(error_logs) > 3:
        suggestions.append("系统可能存在系统性问题，建议进行全面检查")
    
    suggestion_text = ""
    if suggestions:
        suggestion_text = f"\n\n{random_choice(ANSWER_TEMPLATES['suggestion_intro'])}\n" + "\n".join([f"{i+1}. {s}" for i, s in enumerate(suggestions)])
    
    answer = f"{intro}\n\n{log_list}{suggestion_text}"
    return answer, 0.88, error_logs[:5]


def generate_natural_service_answer(question: str, logs: list) -> tuple:
    """生成自然的服务查询回答"""
    service_name = "系统服务"
    service_keywords = {
        "订单": "订单服务",
        "支付": "支付服务", 
        "库存": "库存服务",
        "用户": "用户服务",
        "通知": "通知服务",
        "网关": "API网关"
    }
    
    for kw, name in service_keywords.items():
        if kw in question:
            service_name = name
            break
    
    filtered_logs = [l for l in logs if service_name.replace("服务", "") in l["service"] or 
                     any(kw in l["service"] for kw in ["order", "payment", "inventory", "user", "notification", "gateway"])]
    
    if not filtered_logs:
        return f"{random_choice(ANSWER_TEMPLATES['no_results'])}", 0.8, []
    
    error_count = sum(1 for l in filtered_logs if l["level"] == "ERROR")
    warn_count = sum(1 for l in filtered_logs if l["level"] == "WARN")
    
    status_emoji = "🟢" if error_count == 0 else "🟡" if warn_count > 0 else "🔴"
    status_text = "运行正常" if error_count == 0 else "存在警告" if warn_count > 0 else "存在异常"
    
    intro = random_choice(["我来查看一下", "让我检查一下", "好的，我来看看", "了解，我查一下"])
    log_list = "\n".join([f"- {format_log_message(log)}" for log in filtered_logs[:4]])
    
    answer = f"{intro}{service_name}的情况：\n\n{log_list}\n\n{status_emoji} **服务状态**: {status_text}\n- 错误数量: {error_count}\n- 警告数量: {warn_count}"
    return answer, 0.85, filtered_logs[:5]


def generate_natural_summary_answer(question: str, logs: list) -> tuple:
    """生成自然的摘要回答"""
    intro = random_choice(ANSWER_TEMPLATES["summary_intro"])
    
    stats = f"""📊 **日志统计**:
• 总日志数: {len(logs)}
• 错误: {sum(1 for l in logs if l['level'] == 'ERROR')}
• 警告: {sum(1 for l in logs if l['level'] == 'WARN')}
• 信息: {sum(1 for l in logs if l['level'] == 'INFO')}
• 调试: {sum(1 for l in logs if l['level'] == 'DEBUG')}"""
    
    error_logs = [l for l in logs if l['level'] == 'ERROR']
    anomalies = "\n".join([f"• [{l['service']}] {l['message']}" for l in error_logs]) if error_logs else "✅ 暂无明显异常"
    
    suggestions = ["建议关注order-service的数据库连接问题", "检查payment-service的支付网关状态"]
    
    answer = f"{intro}\n\n{stats}\n\n⚠️ **异常发现**:\n{anomalies}\n\n💡 **建议**:\n{'\n'.join([f'{i+1}. {s}' for i, s in enumerate(suggestions)])}"
    return answer, 0.9, logs[:5]


def generate_natural_trend_answer(question: str, logs: list) -> tuple:
    """生成自然的趋势分析回答"""
    error_count = sum(1 for l in logs if l['level'] == 'ERROR')
    
    if error_count > 3:
        trend = "⚠️ **错误率呈上升趋势**"
        findings = ["• 数据库连接问题频繁出现", "• 支付服务响应延迟", "• 需要关注系统稳定性"]
        measures = ["1. 立即检查数据库连接池配置", "2. 分析慢查询日志", "3. 考虑增加系统资源"]
    else:
        trend = "✅ **系统运行稳定**"
        findings = ["• 错误率在正常范围内", "• 系统运行状态良好"]
        measures = ["1. 保持监控", "2. 定期巡检"]
    
    answer = f"📈 **趋势分析结果**:\n\n{trend}\n\n🔍 **关键发现**:\n{'\n'.join(findings)}\n\n🛡️ **建议措施**:\n{'\n'.join(measures)}"
    return answer, 0.85, logs[:5]


def generate_natural_classify_answer(question: str, logs: list) -> tuple:
    """生成自然的分类回答"""
    classified = classify_logs(logs)
    
    classification = "\n".join([f"• {category}: {len(items)} 条" for category, items in classified.items() if len(items) > 0])
    
    answer = f"📋 **日志分类结果**:\n\n{classification}\n\n每个类别的日志分布清晰，便于针对性分析。"
    return answer, 0.82, logs[:5]


def generate_natural_root_cause_answer(question: str, logs: list) -> tuple:
    """生成自然的根因分析回答"""
    primary_cause, factors, solutions = analyze_root_cause(logs)
    
    answer = f"🎯 **根因分析结果**:\n\n**主要原因**: {primary_cause}\n\n**关联因素**:\n{'\n'.join(factors)}\n\n💡 **修复建议**:\n{'\n'.join(solutions)}"
    return answer, 0.88, logs[:5]


def generate_natural_suggest_answer(question: str, logs: list) -> tuple:
    """生成自然的修复建议回答"""
    error_logs = [l for l in logs if l["level"] == "ERROR"]
    
    if not error_logs:
        return "当前系统运行正常，未检测到需要修复的问题。如有其他需求，请随时告诉我！", 0.85, []
    
    intro = random_choice(ANSWER_TEMPLATES["suggestion_intro"])
    analysis = "检测到以下问题需要关注：\n" + "\n".join([f"• {log['message']}" for log in error_logs[:3]])
    
    solutions = ["检查数据库连接池配置", "分析慢查询日志", "考虑增加系统资源"]
    steps = ["1. 定位问题服务", "2. 分析错误日志", "3. 实施修复", "4. 验证修复效果"]
    
    answer = f"{intro}\n\n💡 **问题分析**:\n{analysis}\n\n📝 **修复方案**:\n{'\n'.join([f'{i+1}. {s}' for i, s in enumerate(solutions)])}\n\n✅ **操作步骤**:\n{'\n'.join(steps)}"
    return answer, 0.85, logs[:5]


def generate_natural_general_answer(question: str, logs: list) -> tuple:
    """生成自然的通用回答"""
    filtered_logs = query_logs(question)
    
    if filtered_logs:
        intro = random_choice(["找到一些相关日志：", "这是相关的日志信息：", "为您找到以下日志："])
        log_list = "\n".join([f"- {format_log_message(log)}" for log in filtered_logs[:5]])
        answer = f"{intro}\n\n{log_list}\n\n如需更详细的分析，请提供更具体的问题，例如：'最近有哪些错误？'、'订单服务的状态如何？'"
    else:
        answer = random_choice(ANSWER_TEMPLATES["no_results"]) + " 您可以尝试问：'最近有哪些错误？'、'帮我总结一下日志'等问题。"
    
    return answer, 0.8, filtered_logs[:5]


def get_current_model() -> str:
    """获取当前使用的模型"""
    return CURRENT_MODEL


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
        self.model = CURRENT_MODEL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer_id": self.answer_id,
            "question": self.question,
            "answer": self.answer,
            "confidence": self.confidence,
            "sources": self.sources,
            "timestamp": self.timestamp,
            "type": self.type,
            "model": self.model
        }


async def call_deepseek_api(prompt: str, context: Optional[str] = None) -> str:
    """调用 DeepSeek API"""
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "your_deepseek_api_key_here":
        raise ValueError("DeepSeek API Key 未配置")

    system_prompt = """你是一个专业的日志分析助手，擅长分析和解读系统日志。请基于提供的日志上下文，用中文简洁、准确地回答用户的问题。

如果提供了日志上下文，请优先基于日志内容回答；如果没有日志上下文，请根据你的知识回答。

回答风格：
- 使用 markdown 格式
- 使用中文
- 保持专业但友好的语气
- 对于错误分析，提供具体的建议
"""

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    if context:
        messages.append({"role": "user", "content": f"日志上下文：\n{context}\n\n问题：{prompt}"})
    else:
        messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=DEEPSEEK_TIMEOUT) as client:
        response = await client.post(
            DEEPSEEK_API_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048
            }
        )

        if response.status_code != 200:
            raise Exception(f"DeepSeek API 调用失败: {response.text}")

        data = response.json()
        return data["choices"][0]["message"]["content"]


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


def classify_logs(logs: List[Dict]) -> Dict[str, List[Dict]]:
    """智能日志分类"""
    classified = {category: [] for category in LOG_CATEGORIES}
    classified["其他"] = []
    
    for log in logs:
        matched = False
        message = log["message"].lower()
        for category, keywords in LOG_CATEGORIES.items():
            for keyword in keywords:
                if keyword.lower() in message or keyword.lower() in log.get("service", "").lower():
                    classified[category].append(log)
                    matched = True
                    break
            if matched:
                break
        if not matched:
            classified["其他"].append(log)
    
    return classified


def analyze_root_cause(logs: List[Dict]) -> tuple:
    """根因分析增强"""
    error_messages = [log["message"] for log in logs if log["level"] == "ERROR"]
    
    primary_cause = "正在分析..."
    factors = []
    solutions = []
    
    # 基于知识库进行根因分析
    for msg in error_messages:
        for problem, info in KNOWLEDGE_BASE.items():
            if problem in msg:
                primary_cause = info["cause"]
                factors = [f"• {problem}"]
                solutions = [f"{i+1}. {s}" for i, s in enumerate(info["solutions"])]
                break
    
    if not primary_cause or primary_cause == "正在分析...":
        # 默认分析逻辑
        db_errors = sum(1 for log in logs if log["level"] == "ERROR" and "数据库" in log["message"])
        if db_errors > 0:
            primary_cause = "数据库连接问题是主要原因"
            factors = ["• 数据库连接池可能耗尽", "• 数据库服务可能不稳定", "• 慢查询导致性能下降"]
            solutions = ["1. 检查数据库连接池配置", "2. 分析慢查询日志", "3. 考虑增加数据库资源"]
        else:
            primary_cause = "系统运行正常，未发现明显根因"
    
    return primary_cause, factors, solutions


def predict_trend(logs: List[Dict], days: int = 7) -> tuple:
    """趋势预测"""
    error_count = sum(1 for log in logs if log["level"] == "ERROR")
    warn_count = sum(1 for log in logs if log["level"] == "WARN")
    
    trend = "稳定"
    risks = []
    measures = []
    
    if error_count > 3:
        trend = "⚠️ 错误率上升趋势"
        risks = ["• 系统稳定性可能下降", "• 用户体验可能受影响", "• 需要关注关键服务"]
        measures = ["1. 立即检查相关服务", "2. 分析错误原因", "3. 实施修复措施"]
    elif warn_count > 5:
        trend = "⚠️ 警告数量较多"
        risks = ["• 潜在问题可能升级", "• 需要预防性维护"]
        measures = ["1. 分析警告原因", "2. 提前采取预防措施"]
    else:
        trend = "✅ 运行稳定"
        risks = ["• 当前无明显风险"]
        measures = ["1. 保持监控", "2. 定期巡检"]
    
    return trend, risks, measures


def generate_classify_answer(question: str) -> tuple:
    """生成日志分类回答"""
    logs = SIMULATED_LOGS
    classified = classify_logs(logs)
    
    classification = "\n".join([f"• {category}: {len(items)} 条" for category, items in classified.items() if len(items) > 0])
    
    details = []
    for category, items in classified.items():
        if items:
            sample = items[:2]
            detail_lines = [f"  - [{item['service']}] {item['message'][:30]}..." for item in sample]
            details.append(f"📁 {category}：\n" + "\n".join(detail_lines))
    
    answer = f"""日志分类结果：

📋 分类统计：
{classification}

🔍 各类别详情：
{"\n\n".join(details)}"""
    
    return answer, 0.85, logs[:5]


def generate_root_cause_answer(question: str) -> tuple:
    """生成根因分析回答"""
    logs = query_logs(question)
    
    primary_cause, factors, solutions = analyze_root_cause(logs)
    
    answer = f"""根因分析结果：

🎯 主要原因：
{primary_cause}

🔗 关联因素：
{"\n".join(factors)}

💡 修复建议：
{"\n".join(solutions)}"""
    
    return answer, 0.88, logs[:5]


def generate_predict_answer(question: str) -> tuple:
    """生成趋势预测回答"""
    logs = SIMULATED_LOGS
    
    trend, risks, measures = predict_trend(logs)
    
    answer = f"""趋势预测结果：

📈 预测趋势：
{trend}

⚠️ 潜在风险：
{"\n".join(risks)}

🛡️ 建议措施：
{"\n".join(measures)}"""
    
    return answer, 0.82, logs[:5]


def generate_suggest_answer(question: str) -> tuple:
    """生成智能修复建议回答"""
    logs = query_logs(question)
    error_logs = [log for log in logs if log["level"] == "ERROR"]
    
    if not error_logs:
        return "当前系统运行正常，未检测到需要修复的问题。", 0.8, []
    
    # 基于知识库生成修复建议
    analysis = "检测到以下问题需要关注：\n" + "\n".join([f"• {log['message']}" for log in error_logs[:3]])
    
    solutions = []
    steps = []
    
    # 查找知识库匹配
    for log in error_logs:
        for problem, info in KNOWLEDGE_BASE.items():
            if problem in log["message"]:
                solutions.extend(info["solutions"])
                steps.extend(info["steps"])
                break
    
    if not solutions:
        solutions = ["检查相关服务状态", "查看详细错误日志", "联系运维人员"]
        steps = ["1. 定位问题服务", "2. 分析错误日志", "3. 实施修复", "4. 验证修复效果"]
    
    # 去重
    solutions = list(dict.fromkeys(solutions))[:3]
    steps = list(dict.fromkeys(steps))[:4]
    
    answer = f"""智能修复建议：

💡 问题分析：
{analysis}

📝 修复方案：
{"\n".join([f"{i+1}. {s}" for i, s in enumerate(solutions)])}

✅ 操作步骤：
{"\n".join(steps)}"""
    
    return answer, 0.85, logs[:5]


def generate_local_answer(question: str) -> tuple:
    """使用本地逻辑生成回答"""
    question_type = analyze_question(question)
    
    if question_type == "error_query":
        return generate_error_answer(question)
    elif question_type == "service_query":
        return generate_service_answer(question)
    elif question_type == "time_query":
        return generate_time_answer(question)
    elif question_type == "summary":
        return generate_summary_answer(question)
    elif question_type == "trend":
        return generate_trend_answer(question)
    elif question_type == "classify":
        return generate_classify_answer(question)
    elif question_type == "root_cause":
        return generate_root_cause_answer(question)
    elif question_type == "predict":
        return generate_predict_answer(question)
    elif question_type == "suggest":
        return generate_suggest_answer(question)
    else:
        return generate_general_answer(question)


async def generate_answer(question: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """生成AI回答，优先使用DeepSeek，失败回退到本地智能逻辑"""
    result = QAAnswer()
    result.question = question
    
    try:
        # 获取日志数据
        logs = query_logs(question)
        
        # 获取对话上下文
        conversation_context = get_conversation_context()
        
        # 优先尝试使用 DeepSeek（如果配置了API key）
        if CURRENT_MODEL == "deepseek":
            try:
                # 构建完整上下文（包括对话历史）
                log_context = "\n".join([f"[{log['timestamp']}] [{log['service']}] [{log['level']}] {log['message']}" for log in logs])
                full_context = f"对话历史：\n{conversation_context}\n\n最新日志：\n{log_context}" if conversation_context else log_context
                
                answer = await call_deepseek_api(question, full_context)
                result.answer = answer
                result.confidence = 0.95
                result.type = "llm"
                result.sources = logs[:5]
                result.model = "deepseek"
                # 保存对话历史
                add_conversation(question, answer)
                return result.to_dict()
            except Exception as llm_error:
                # DeepSeek 调用失败，回退到本地逻辑
                result.model = "local (fallback)"
        
        # 使用本地智能逻辑生成自然回答
        answer, confidence, sources = generate_natural_answer(question, logs)
        result.answer = answer
        result.confidence = confidence
        result.type = analyze_question(question)
        result.sources = sources
        result.model = "local"
        # 保存对话历史（本地模式）
        add_conversation(question, answer)
        
    except Exception as e:
        result.answer = f"抱歉，我无法回答这个问题。错误信息：{str(e)}"
        result.confidence = 0.0
        result.model = "local"
    
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
