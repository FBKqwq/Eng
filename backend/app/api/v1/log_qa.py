"""AI日志问答 API - AI增强版

接口：
- POST /api/v1/log_qa/ask - AI日志问答
- GET /api/v1/log_qa/history - 获取对话历史
- GET /api/v1/log_qa/model - 获取当前使用的模型信息
- GET /api/v1/log_qa/classify - 智能日志分类
- GET /api/v1/log_qa/root_cause - 根因分析
- GET /api/v1/log_qa/predict - 趋势预测
- GET /api/v1/log_qa/suggest - 智能修复建议

统一信封：ApiResponse[LogQAAnswer]
"""

from fastapi import APIRouter, Query

from app.schemas.response import ApiCode, ApiResponse, error_envelope, ok_envelope
from app.schemas.log_qa import LogQARequest, LogQAAnswer
from app.services.yc.ym.log_qa_agent import (
    generate_answer, 
    get_conversation_history, 
    get_current_model,
    classify_logs,
    analyze_root_cause,
    predict_trend,
    SIMULATED_LOGS
)

router = APIRouter()


@router.post("/ask", response_model=ApiResponse[LogQAAnswer])
async def ask(request: LogQARequest) -> ApiResponse[LogQAAnswer]:
    """AI日志问答"""
    result = await generate_answer(request.question, request.context)
    return ok_envelope(result)


@router.get("/model")
def get_model_info() -> ApiResponse[dict]:
    """获取当前使用的模型信息"""
    model = get_current_model()
    return ok_envelope({"model": model, "is_llm": model == "deepseek"})


@router.get("/history")
def get_history(limit: int = Query(default=10, ge=1, le=50)) -> ApiResponse[list]:
    """获取对话历史"""
    history = get_conversation_history(limit=limit)
    return ok_envelope(history)


@router.get("/classify")
def classify_logs_api() -> ApiResponse[dict]:
    """智能日志分类"""
    result = classify_logs(SIMULATED_LOGS)
    return ok_envelope(result)


@router.get("/root_cause")
def root_cause_analysis() -> ApiResponse[dict]:
    """根因分析"""
    primary_cause, factors, solutions = analyze_root_cause(SIMULATED_LOGS)
    return ok_envelope({
        "primary_cause": primary_cause,
        "factors": factors,
        "solutions": solutions
    })


@router.get("/predict")
def trend_prediction(days: int = Query(default=7, ge=1, le=30)) -> ApiResponse[dict]:
    """趋势预测"""
    trend, risks, measures = predict_trend(SIMULATED_LOGS, days)
    return ok_envelope({
        "trend": trend,
        "risks": risks,
        "measures": measures,
        "prediction_days": days
    })


@router.get("/suggest")
def smart_suggestions() -> ApiResponse[dict]:
    """智能修复建议"""
    error_logs = [log for log in SIMULATED_LOGS if log["level"] == "ERROR"]
    
    if not error_logs:
        return ok_envelope({
            "analysis": "当前系统运行正常，未检测到需要修复的问题。",
            "solutions": [],
            "steps": []
        })
    
    # 基于知识库生成修复建议
    from app.services.yc.ym.log_qa_agent import KNOWLEDGE_BASE
    
    analysis = "检测到以下问题需要关注：\n" + "\n".join([f"• {log['message']}" for log in error_logs[:3]])
    
    solutions = []
    steps = []
    
    for log in error_logs:
        for problem, info in KNOWLEDGE_BASE.items():
            if problem in log["message"]:
                solutions.extend(info["solutions"])
                steps.extend(info["steps"])
                break
    
    if not solutions:
        solutions = ["检查相关服务状态", "查看详细错误日志", "联系运维人员"]
        steps = ["1. 定位问题服务", "2. 分析错误日志", "3. 实施修复", "4. 验证修复效果"]
    
    solutions = list(dict.fromkeys(solutions))[:3]
    steps = list(dict.fromkeys(steps))[:4]
    
    return ok_envelope({
        "analysis": analysis,
        "solutions": solutions,
        "steps": steps
    })
