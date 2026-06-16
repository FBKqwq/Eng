"""预警去重与幂等（占位）。

职责：幂等键 = alert_type + affected_service + 时间桶；重复则累加 evidence_count。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §1.3 / §3.2
状态：占位 — 待 M5 实现。
"""

from __future__ import annotations

from typing import Any


def check_duplicate(alert_candidate: dict[str, Any], *, bucket_minutes: int = 10) -> dict[str, Any]:
  """检查是否重复预警（占位）。"""
  return {
    "ok": False,
    "placeholder": True,
    "message": "check_duplicate 尚未实现",
    "is_duplicate": False,
    "existing_alert_id": None,
    "bucket_minutes": bucket_minutes,
  }


def build_idempotency_key(alert_candidate: dict[str, Any], *, bucket_minutes: int = 10) -> str:
  """构建幂等键（占位）。"""
  alert_type = alert_candidate.get("alert_type", "unknown")
  service = alert_candidate.get("affected_service", "unknown")
  return f"{alert_type}:{service}:bucket_{bucket_minutes}"
