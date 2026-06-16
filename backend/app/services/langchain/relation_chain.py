"""隐藏关系发现 Chain（占位）。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.4 analyze_relations 节点
状态：占位 — 待 M7 实现；定时子图可先跳过此节点。
"""

from __future__ import annotations

from typing import Any


def discover_relations(evidence_package: dict[str, Any]) -> dict[str, Any]:
    """发现如「高峰后支付失败上升」类隐藏关系（占位）。"""
    return {
        "ok": False,
        "placeholder": True,
        "message": "relation_chain 尚未实现",
        "relations": [],
    }
