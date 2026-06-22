"""预警读写 Agent 工具。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §3.2 工具 7-8 / 16
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.services.alert import alert_service
from app.services.alert import dedup


class WriteAlertInput(BaseModel):
  alert: dict[str, Any]


class CheckDuplicateInput(BaseModel):
  alert_candidate: dict[str, Any]
  bucket_minutes: int = 10


def alert_write_event(params: WriteAlertInput) -> dict[str, Any]:
  """工具 7：写预警（写类，仅 persist 节点调用）。"""
  try:
    result = alert_service.write_alert(params.alert)
    response: dict[str, Any] = {**result, "tool": "alert_write_event"}
    response.pop("placeholder", None)
    return response
  except Exception as exc:
    return {
      "ok": False,
      "error": str(exc),
      "tool": "alert_write_event",
    }


def alert_check_duplicate(params: CheckDuplicateInput) -> dict[str, Any]:
  """工具 8：预警去重检查。"""
  try:
    result = dedup.check_duplicate(
      params.alert_candidate,
      bucket_minutes=params.bucket_minutes,
    )
    response: dict[str, Any] = {**result, "tool": "alert_check_duplicate"}
    response.pop("placeholder", None)
    return response
  except Exception as exc:
    return {
      "ok": False,
      "error": str(exc),
      "tool": "alert_check_duplicate",
      "is_duplicate": False,
    }


def alert_list_active(limit: int = 50) -> dict[str, Any]:
  """工具 16：查询活跃预警（第二阶段，尚未实装）。"""
  return {
    "ok": False,
    "tool": "alert_list_active",
    "items": [],
    "limit": limit,
    "message": "alert_list_active 属第二阶段，尚未实装",
  }
