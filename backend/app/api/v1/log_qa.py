"""AI日志问答 API

接口：POST /api/v1/log_qa/ask、GET /api/v1/log_qa/history
统一信封：ApiResponse[LogQAAnswer]
"""

from fastapi import APIRouter, Query

from app.schemas.response import ApiCode, ApiResponse, error_envelope, ok_envelope
from app.schemas.log_qa import LogQARequest, LogQAAnswer
from app.services.yc.ym.log_qa_agent import generate_answer, get_conversation_history

router = APIRouter()


@router.post("/ask", response_model=ApiResponse[LogQAAnswer])
def ask(request: LogQARequest) -> ApiResponse[LogQAAnswer]:
    """AI日志问答"""
    result = generate_answer(request.question, request.context)
    return ok_envelope(result)


@router.get("/history")
def get_history(limit: int = Query(default=10, ge=1, le=50)) -> ApiResponse[list]:
    """获取对话历史"""
    history = get_conversation_history(limit=limit)
    return ok_envelope(history)
