"""智能根因分析 API

接口：POST /api/v1/root_cause/analyze、GET /api/v1/root_cause/history、POST /api/v1/root_cause/{id}/feedback
统一信封：ApiResponse[RootCauseAnalysisResponse]
"""

from fastapi import APIRouter, Query

from app.schemas.response import ApiCode, ApiResponse, error_envelope, ok_envelope
from app.schemas.root_cause import (
    RootCauseAnalysisRequest,
    RootCauseAnalysisResponse,
    SolutionFeedbackRequest,
)
from app.services.yc.yl.root_cause_analyzer import (
    analyze_root_cause,
    get_analysis_history,
    validate_solution,
)

router = APIRouter()


@router.post("/analyze", response_model=ApiResponse[RootCauseAnalysisResponse])
def analyze(request: RootCauseAnalysisRequest) -> ApiResponse[RootCauseAnalysisResponse]:
    """执行智能根因分析"""
    result = analyze_root_cause(request.problem_description, request.context)
    
    if result.get("status") == "failed":
        return error_envelope(ApiCode.QUERY_FAILED, result.get("summary", "分析失败"))
    
    return ok_envelope(result)


@router.get("/history")
def get_history(limit: int = Query(default=10, ge=1, le=50)) -> ApiResponse[list]:
    """获取分析历史记录"""
    history = get_analysis_history(limit=limit)
    return ok_envelope(history)


@router.post("/{analysis_id}/feedback")
def feedback(
    analysis_id: str,
    request: SolutionFeedbackRequest,
) -> ApiResponse[dict]:
    """提交解决方案反馈"""
    result = validate_solution(analysis_id, request.solution_index, request.feedback)
    if result.get("ok"):
        return ok_envelope(result)
    return error_envelope(ApiCode.OPERATION_FAILED, "反馈提交失败")
