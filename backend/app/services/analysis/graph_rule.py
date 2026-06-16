"""规则任务子图（占位）。

职责：关键错误即时深挖；由 trigger_scanner 周期扫描触发。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.5
状态：占位 — 待 M5 实现最小版。

节点流：parse_trigger_event -> fetch_context -> correlate_events -> build_evidence
       -> infer_root_cause -> assess_severity -> generate_event_report
"""

from __future__ import annotations

from typing import Any


def build_rule_graph() -> Any:
    """构建规则子图（占位）。"""
    return None


def run_rule_subgraph(trigger_event: dict[str, Any]) -> dict[str, Any]:
    """执行规则子图（占位）。"""
    return {
        "ok": False,
        "placeholder": True,
        "message": "graph_rule 尚未实现，待 M5 实现",
        "trigger_event_id": trigger_event.get("log_id"),
    }
