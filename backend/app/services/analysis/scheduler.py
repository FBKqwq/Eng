"""定时分析调度器。

职责：按 analysis_schedule_minutes 周期触发主图 scheduled 路径；窗口对齐与防重叠。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.6
"""

from __future__ import annotations

from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.services.analysis.graph_main import run_main_graph

_JOB_ID = "analysis_scheduled"
_scheduler: BackgroundScheduler | None = None


def run_once(time_window: dict[str, Any] | None = None) -> dict[str, Any]:
    """执行一次定时主图（持久化由主图 persist_result 收口）。"""
    node_trace: list[Any] = []
    try:
        result = run_main_graph("scheduled", time_window=time_window)
        node_trace = list(result.get("node_trace") or [])

        if not result.get("ok"):
            return {
                "ok": False,
                "report_id": result.get("report_id"),
                "node_trace": node_trace,
                "error": "main graph execution failed",
                "errors": list(result.get("errors") or []),
            }

        response: dict[str, Any] = {
            "ok": True,
            "report_id": result.get("report_id"),
            "node_trace": node_trace,
        }
        alert_id = result.get("alert_id")
        if alert_id is not None:
            response["alert_id"] = alert_id
        return response
    except Exception as exc:  # noqa: BLE001 — 结构化错误，不向上抛裸异常
        return {
            "ok": False,
            "report_id": None,
            "node_trace": node_trace,
            "error": str(exc),
        }


def _scheduled_job() -> None:
    """APScheduler 回调：单次调度异常不影响后续周期。"""
    try:
        run_once()
    except Exception:
        pass


def start_scheduler() -> dict[str, Any]:
    """启动定时调度（APScheduler，防重叠 max_instances=1）。"""
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        return {
            "ok": True,
            "running": True,
            "interval_minutes": settings.analysis_schedule_minutes,
            "message": "scheduler already running",
        }

    try:
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            _scheduled_job,
            trigger="interval",
            minutes=settings.analysis_schedule_minutes,
            id=_JOB_ID,
            max_instances=1,
            replace_existing=True,
        )
        scheduler.start()
        _scheduler = scheduler
        return {
            "ok": True,
            "running": True,
            "interval_minutes": settings.analysis_schedule_minutes,
        }
    except Exception as exc:  # noqa: BLE001
        _scheduler = None
        return {
            "ok": False,
            "running": False,
            "error": str(exc),
        }


def stop_scheduler() -> dict[str, Any]:
    """停止定时调度。"""
    global _scheduler

    if _scheduler is None or not _scheduler.running:
        _scheduler = None
        return {
            "ok": True,
            "running": False,
            "message": "scheduler not running",
        }

    try:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        return {
            "ok": True,
            "running": False,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "running": False,
            "error": str(exc),
        }
