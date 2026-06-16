"""定时分析调度器（占位）。

职责：按 ANALYSIS_SCHEDULE_MINUTES 周期触发定时子图；窗口对齐与防重叠。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.6
状态：占位 — 待 M4/M5 实现 APScheduler 或 asyncio task。
"""

from __future__ import annotations

from typing import Any


def start_scheduler() -> dict[str, Any]:
    """启动定时调度（占位）。"""
    return {
        "ok": False,
        "placeholder": True,
        "message": "scheduler 尚未实现，待 M4 配置 ANALYSIS_SCHEDULE_MINUTES",
    }


def stop_scheduler() -> dict[str, Any]:
    """停止定时调度（占位）。"""
    return {"ok": False, "placeholder": True, "message": "scheduler 未运行"}
