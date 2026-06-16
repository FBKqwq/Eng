"""定时任务子图（占位）。

职责：平台周期体检 + 业务洞察；每 15 分钟触发。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.4
状态：占位 — 待 M4 实现最小版（聚合 -> 证据 -> 报告）。

节点流：build_time_window -> plan_queries -> aggregate_metrics -> sample_logs
       -> build_evidence -> analyze_relations -> generate_report
"""

from __future__ import annotations

from typing import Any


def build_scheduled_graph() -> Any:
    """构建定时子图（占位）。"""
    return None


def run_scheduled_subgraph(time_window: dict[str, Any] | None = None) -> dict[str, Any]:
    """执行定时子图（占位）。"""
    return {
        "ok": False,
        "placeholder": True,
        "message": "graph_scheduled 尚未实现，待 M4 实现",
        "time_window": time_window or {},
    }
