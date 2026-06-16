"""报告读写 Agent 工具（占位）。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §3.2 工具 6 / 15
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class WriteReportInput(BaseModel):
  report: dict[str, Any]


def analysis_write_report(params: WriteReportInput) -> dict[str, Any]:
  """工具 6：写报告（写类，仅 persist 节点调用）（占位）。"""
  return {
    "ok": False,
    "placeholder": True,
    "tool": "analysis_write_report",
    "message": "待 M4 接入 report_service.write_report",
  }


def report_list_recent(limit: int = 20) -> dict[str, Any]:
  """工具 15：查询最近报告（第二阶段）（占位）。"""
  return {
    "ok": False,
    "placeholder": True,
    "tool": "report_list_recent",
    "limit": limit,
  }
