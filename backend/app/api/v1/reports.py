"""分析报告 API。

规划：GET /api/v1/reports/recent、GET /api/v1/reports/{id}
"""

from fastapi import APIRouter, Query

from app.schemas.report import ReportDetailResponse, ReportListResponse
from app.services.report.report_service import get_report, list_recent_reports

router = APIRouter()


@router.get("/recent", response_model=ReportListResponse)
def recent_reports(limit: int = Query(default=20, ge=1, le=100)) -> dict:
  result = list_recent_reports(limit=limit)
  return ReportListResponse(
    ok=result.get("ok", False),
    placeholder=False,
    message=result.get("message") or result.get("error", ""),
    items=result.get("items", []),
    total=result.get("total", 0),
    limit=result.get("limit", limit),
  ).model_dump()


@router.get("/{report_id}", response_model=ReportDetailResponse)
def report_detail(report_id: str) -> dict:
  result = get_report(report_id)
  # 未命中：service 返回 ok=True 且 report=None，保持结构化响应而非 HTTP 404
  return ReportDetailResponse(
    ok=result.get("ok", False),
    placeholder=False,
    message=result.get("message") or result.get("error", ""),
    report_id=result.get("report_id", report_id),
    report=result.get("report"),
  ).model_dump()
