"""报告读写 Agent 工具。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §3.2 工具 6 / 15
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.services.report.report_service import write_report


class WriteReportInput(BaseModel):
  report: dict[str, Any]


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


def report_list_recent(limit: int = 20) -> dict[str, Any]:
  """工具 15：查询最近报告（第二阶段 M7，当前未实装）。"""
  return {
    "ok": False,
    "tool": "report_list_recent",
    "limit": limit,
    "message": "第二阶段 M7 实装，当前未接入 report_service.list_recent_reports",
  }
