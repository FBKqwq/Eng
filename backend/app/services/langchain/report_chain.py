"""周期报告 Chain（占位）。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.4 generate_report 节点
状态：占位 — 待 M3/M4 实现；LLM 不可用时退化为纯统计报告。
"""

from __future__ import annotations

from typing import Any


def generate_periodic_report(evidence_package: dict[str, Any]) -> dict[str, Any]:
    """基于证据包生成周期分析报告（占位）。"""
    return {
        "ok": False,
        "placeholder": True,
        "message": "report_chain 尚未实现",
        "report_type": "periodic",
        "risk_level": "unknown",
        "summary": "占位：待接入 LLM 或降级模板",
    }
