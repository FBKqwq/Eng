"""规则触发扫描器（占位）。

职责：周期扫描 ES 中命中 trigger_subgraph=True 规则的日志，去重后触发规则子图。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.5 / §2.6
状态：占位 — 待 M5 实现；第一版轮询 TRIGGER_SCAN_SECONDS。
"""

from __future__ import annotations

from typing import Any


def start_trigger_scanner() -> dict[str, Any]:
    """启动规则扫描循环（占位）。"""
    return {
        "ok": False,
        "placeholder": True,
        "message": "trigger_scanner 尚未实现，待 M5 配置 TRIGGER_SCAN_SECONDS",
    }


def scan_once() -> dict[str, Any]:
    """执行一次规则扫描（占位）。"""
    return {
        "ok": False,
        "placeholder": True,
        "message": "scan_once 尚未实现",
        "triggered_count": 0,
    }
