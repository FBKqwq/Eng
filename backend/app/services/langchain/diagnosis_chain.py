"""事件根因诊断 Chain（占位）。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.5 infer_root_cause 节点
状态：占位 — 待 M3/M5 实现。
"""

from __future__ import annotations

from typing import Any


def infer_root_cause(evidence_package: dict[str, Any]) -> dict[str, Any]:
    """基于证据包推断根因（占位）。"""
    return {
        "ok": False,
        "placeholder": True,
        "message": "diagnosis_chain 尚未实现",
        "root_cause": None,
        "confidence": 0.0,
    }


def generate_event_report(evidence_package: dict[str, Any]) -> dict[str, Any]:
    """生成事件诊断报告（占位，可与 infer_root_cause 合并为一次调用）。"""
    return {
        "ok": False,
        "placeholder": True,
        "message": "generate_event_report 尚未实现",
        "report_type": "event",
    }
