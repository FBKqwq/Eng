"""分析报告持久化（占位）。

职责：写入/查询 analysis-results-* 索引。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §1.3 report 域
状态：占位 — 待 M4 实现。
"""

from __future__ import annotations

from typing import Any


def write_report(report: dict[str, Any]) -> dict[str, Any]:
  """写入分析报告（占位）。"""
  return {
    "ok": False,
    "placeholder": True,
    "message": "write_report 尚未实现，待 M4 创建 analysis-results-* 索引",
    "report_id": None,
  }


def list_recent_reports(limit: int = 20, report_type: str | None = None) -> dict[str, Any]:
  """查询最近报告列表（占位）。"""
  return {
    "ok": False,
    "placeholder": True,
    "message": "list_recent_reports 尚未实现",
    "items": [],
    "total": 0,
    "limit": limit,
    "report_type": report_type,
  }


def get_report(report_id: str) -> dict[str, Any]:
  """按 ID 查询单份报告（占位）。"""
  return {
    "ok": False,
    "placeholder": True,
    "message": "get_report 尚未实现",
    "report_id": report_id,
    "report": None,
  }
