"""预警读写 Agent 工具（占位）。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §3.2 工具 7-8 / 16
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class WriteAlertInput(BaseModel):
  alert: dict[str, Any]


class CheckDuplicateInput(BaseModel):
  alert_candidate: dict[str, Any]
  bucket_minutes: int = 10


def alert_write_event(params: WriteAlertInput) -> dict[str, Any]:
  """工具 7：写预警（写类，仅 persist 节点调用）（占位）。"""
  return {
    "ok": False,
    "placeholder": True,
    "tool": "alert_write_event",
    "message": "待 M5 接入 alert_service.write_alert",
  }


def alert_check_duplicate(params: CheckDuplicateInput) -> dict[str, Any]:
  """工具 8：预警去重检查（占位）。"""
  return {
    "ok": False,
    "placeholder": True,
    "tool": "alert_check_duplicate",
    "is_duplicate": False,
  }


def alert_list_active(limit: int = 50) -> dict[str, Any]:
  """工具 16：查询活跃预警（第二阶段）（占位）。"""
  return {
    "ok": False,
    "placeholder": True,
    "tool": "alert_list_active",
    "items": [],
    "limit": limit,
  }
