"""证据包压缩构建（占位）。

职责：原始日志 → 过滤 → 分组 → 采样 → 证据包；控制进入 LLM 的 token 量。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.6
状态：占位 — 待 M3 实现。
"""

from __future__ import annotations

from typing import Any


def build_evidence_package(
    raw_logs: list[dict[str, Any]],
    metrics: dict[str, Any] | None = None,
    *,
    max_logs: int = 50,
) -> dict[str, Any]:
    """将原始日志与聚合指标压缩为证据包（占位）。"""
    return {
        "ok": False,
        "placeholder": True,
        "message": "evidence_builder 尚未实现",
        "input_log_count": len(raw_logs),
        "max_logs": max_logs,
        "metrics_keys": list((metrics or {}).keys()),
        "evidence_package": {},
    }
