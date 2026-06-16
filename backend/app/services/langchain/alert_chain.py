"""预警解释 Chain（占位）。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.3 alert_decision 节点
状态：占位 — 待 M3 实现。
"""

from __future__ import annotations

from typing import Any


def explain_alert(alert_candidate: dict[str, Any]) -> dict[str, Any]:
    """为候选预警生成可解释文案（占位）。"""
    return {
        "ok": False,
        "placeholder": True,
        "message": "alert_chain 尚未实现",
        "title": None,
        "detail": None,
    }
