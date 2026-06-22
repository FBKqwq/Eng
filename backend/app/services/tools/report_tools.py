"""报告读写 Agent 工具。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §3.2 工具 6 / 15
"""

from __future__ import annotations

from typing import Any

from typing import Optional

from pydantic import BaseModel, Field

from app.services.report.report_service import list_recent_reports, write_report

MAX_LIST_LIMIT = 50


class WriteReportInput(BaseModel):
  report: dict[str, Any]


class ReportListRecentInput(BaseModel):
  limit: int = Field(default=20, le=MAX_LIST_LIMIT)
  report_type: Optional[str] = None


def analysis_write_report(params: WriteReportInput) -> dict[str, Any]:
  """工具 6：写报告（写类，仅 persist 节点 / include_write_tools=True 时暴露）。"""
  tool = "analysis_write_report"
  try:
    result = write_report(params.report)
    response: dict[str, Any] = {**result, "tool": tool}
    response.pop("placeholder", None)
    return response
  except Exception as exc:
    return {
      "ok": False,
      "error": str(exc),
      "tool": tool,
    }


def report_list_recent(params: ReportListRecentInput) -> dict[str, Any]:
  """工具 15：查询最近报告（只读，薄包装 report_service.list_recent_reports）。"""
  tool = "report_list_recent"
  try:
    result = list_recent_reports(limit=params.limit, report_type=params.report_type)
    response: dict[str, Any] = {**result, "tool": tool}
    response.pop("placeholder", None)
    return response
  except Exception as exc:
    return {
      "ok": False,
      "error": str(exc),
      "tool": tool,
      "items": [],
      "total": 0,
      "limit": params.limit,
    }
