"""系统健康检查 Agent 工具（占位）。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §3.2 工具 9
组合：elasticsearch/cluster_status + kafka/cluster_status + docker_status
"""

from __future__ import annotations

from typing import Any


def system_health_check() -> dict[str, Any]:
  """工具 9：组合系统健康快照（占位）。"""
  return {
    "ok": False,
    "placeholder": True,
    "tool": "system_health_check",
    "message": "待 M2 组合 ES/Kafka/Docker 健康探测",
    "elasticsearch": {"available": False},
    "kafka": {"available": False},
    "docker": {"available": False},
  }
