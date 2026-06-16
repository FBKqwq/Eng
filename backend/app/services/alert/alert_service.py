"""预警持久化（占位）。

职责：写入/查询 alerts-* 索引；状态机 active -> acknowledged -> resolved。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §1.3 alert 域
状态：占位 — 待 M5 实现。
"""

from __future__ import annotations

from typing import Any

AlertStatus = str  # active | acknowledged | resolved


def write_alert(alert: dict[str, Any]) -> dict[str, Any]:
  """写入预警事件（占位）。"""
  return {
    "ok": False,
    "placeholder": True,
    "message": "write_alert 尚未实现，待 M5 创建 alerts-* 索引",
    "alert_id": None,
  }


def list_active_alerts(limit: int = 50) -> dict[str, Any]:
  """查询活跃预警列表（占位）。"""
  return {
    "ok": False,
    "placeholder": True,
    "message": "list_active_alerts 尚未实现",
    "items": [],
    "total": 0,
    "limit": limit,
  }


def acknowledge_alert(alert_id: str, operator: str | None = None) -> dict[str, Any]:
  """确认预警（占位）。"""
  return {
    "ok": False,
    "placeholder": True,
    "message": "acknowledge_alert 尚未实现",
    "alert_id": alert_id,
    "operator": operator,
  }
