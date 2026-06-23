"""分析报告 API。

接口：GET /api/v1/reports/recent、GET /api/v1/reports/{id}
统一信封：ApiResponse[ReportListData] / ApiResponse[ReportDetailData]
"""

from fastapi import APIRouter, Query

from app.schemas.report import ReportDetailData, ReportListData
from app.schemas.response import ApiCode, ApiResponse, error_envelope, ok_envelope
from app.services.report.report_service import get_report, list_recent_reports

router = APIRouter()


@router.get("/recent", response_model=ApiResponse[ReportListData])
def recent_reports(limit: int = Query(default=20, ge=1, le=100)) -> ApiResponse[ReportListData]:
  result = list_recent_reports(limit=limit)
  if not result.get("ok"):
    return error_envelope(ApiCode.QUERY_FAILED, result.get("error") or result.get("message", ""))
  return ok_envelope(
    ReportListData(
      items=result.get("items", []),
      total=result.get("total", 0),
      limit=result.get("limit", limit),
    )
  )


@router.get("/{report_id}", response_model=ApiResponse[ReportDetailData])
def report_detail(report_id: str) -> ApiResponse[ReportDetailData]:
  result = get_report(report_id)
  # 未命中：service 返回 ok=True 且 report=None，仍以 200 + 结构化响应返回（非 HTTP 404）
  if not result.get("ok"):
    return error_envelope(
      ApiCode.QUERY_FAILED,
      result.get("error") or result.get("message", ""),
      data=ReportDetailData(report_id=report_id, report=None),
    )
  return ok_envelope(
    ReportDetailData(report_id=result.get("report_id", report_id), report=result.get("report"))
  )
