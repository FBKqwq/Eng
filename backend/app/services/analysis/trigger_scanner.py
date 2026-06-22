"""规则触发扫描器。

职责：周期扫描 ES 中命中 trigger_subgraph=True 规则的日志，委托主图完成分析与持久化。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.5 / §2.6
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.schemas.log import LogLevel, LogQueryRequest, SortOrder
from app.services.analysis.graph_main import run_main_graph
from app.services.diagnosis.rule_engine import match_log
from app.services.elasticsearch import log_query_service

_JOB_ID = "trigger_scanner"
_scheduler: BackgroundScheduler | None = None
_SCAN_PAGE_SIZE = 100


def scan_once() -> dict[str, Any]:
    """执行一次规则扫描：查询触发日志 → match_log 复核 → 委托主图持久化。"""
    alert_ids: list[str] = []
    report_ids: list[str] = []
    triggered_count = 0
    errors: list[str] = []

    try:
        fetch_result = _fetch_candidate_logs()
    except Exception as exc:  # noqa: BLE001 — 结构化错误，不向上抛裸异常
        return _scan_error(str(exc))

    if not fetch_result.get("ok"):
        return _scan_error(str(fetch_result.get("error") or "日志查询失败"))

    seen_log_ids: set[str] = set()
    for item in fetch_result.get("items") or []:
        log_event = _item_to_log_event(item)
        log_id = _coerce_str(log_event.get("log_id")).strip()
        if log_id and log_id in seen_log_ids:
            continue
        if log_id:
            seen_log_ids.add(log_id)

        match_result = match_log(log_event)
        if not match_result.get("matched") or not match_result.get("trigger_subgraph"):
            continue

        process_result = _process_trigger_log(log_event, match_result)
        if process_result.get("triggered"):
            triggered_count += 1
            report_id = process_result.get("report_id")
            alert_id = process_result.get("alert_id")
            if report_id:
                report_ids.append(report_id)
            if alert_id:
                alert_ids.append(alert_id)
        elif process_result.get("error"):
            errors.append(str(process_result["error"]))

    response: dict[str, Any] = {
        "ok": True,
        "triggered_count": triggered_count,
        "alert_ids": alert_ids,
        "report_ids": report_ids,
    }
    if errors:
        response["errors"] = errors
    return response


def start_trigger_scanner() -> dict[str, Any]:
    """启动规则扫描循环（APScheduler，防重叠 max_instances=1）。"""
    global _scheduler

    interval_seconds = max(1, int(settings.trigger_scan_seconds))
    if _scheduler is not None and _scheduler.running:
        return {
            "ok": True,
            "running": True,
            "interval_seconds": interval_seconds,
            "message": "trigger_scanner already running",
        }

    try:
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            _scheduled_job,
            trigger="interval",
            seconds=interval_seconds,
            id=_JOB_ID,
            max_instances=1,
            replace_existing=True,
        )
        scheduler.start()
        _scheduler = scheduler
        return {
            "ok": True,
            "running": True,
            "interval_seconds": interval_seconds,
        }
    except Exception as exc:  # noqa: BLE001
        _scheduler = None
        return {
            "ok": False,
            "running": False,
            "error": str(exc),
        }


def stop_trigger_scanner() -> dict[str, Any]:
    """停止规则扫描循环。"""
    global _scheduler

    if _scheduler is None or not _scheduler.running:
        _scheduler = None
        return {
            "ok": True,
            "running": False,
            "message": "trigger_scanner not running",
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


def _scheduled_job() -> None:
    """APScheduler 回调：单次扫描异常不影响后续周期。"""
    try:
        scan_once()
    except Exception:
        pass


def _fetch_candidate_logs() -> dict[str, Any]:
    """查询最近窗口内可能命中规则的日志（ERROR + 已知 trigger error_code）。"""
    window_seconds = max(1, int(settings.trigger_scan_seconds))
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(seconds=window_seconds)

    request = LogQueryRequest(
        start_time=start_time.replace(tzinfo=None),
        end_time=end_time.replace(tzinfo=None),
        log_levels=[LogLevel.error, LogLevel.critical],
        page=1,
        page_size=_SCAN_PAGE_SIZE,
        sort_by="timestamp",
        sort_order=SortOrder.desc,
    )
    result = log_query_service.search_logs(request)
    if not result.get("available"):
        return {
            "ok": False,
            "error": str(result.get("error") or "ES 不可用"),
            "items": [],
        }
    return {
        "ok": True,
        "items": list(result.get("items") or []),
    }


def _process_trigger_log(
    log_event: dict[str, Any],
    match_result: dict[str, Any],
) -> dict[str, Any]:
    """单条触发日志：委托主图完成子图、去重与持久化。"""
    trigger_event = dict(log_event)
    trigger_event["trigger_rule"] = {
        "rule_id": match_result.get("rule_id"),
        "rule_name": match_result.get("rule_name"),
        "severity": match_result.get("severity"),
    }

    try:
        graph_result = run_main_graph("rule", trigger_event=trigger_event)
    except Exception as exc:  # noqa: BLE001
        return {"triggered": False, "error": f"主图执行异常: {exc}"}

    if not graph_result.get("ok"):
        error_msg = "主图执行失败"
        graph_errors = graph_result.get("errors") or []
        if graph_errors:
            first = graph_errors[0]
            if isinstance(first, dict) and first.get("message"):
                error_msg = str(first["message"])
            elif isinstance(first, str):
                error_msg = first
        return {"triggered": False, "error": error_msg}

    return {
        "triggered": True,
        "report_id": graph_result.get("report_id"),
        "alert_id": graph_result.get("alert_id"),
    }


def _item_to_log_event(item: dict[str, Any]) -> dict[str, Any]:
    payload = item.get("payload")
    if isinstance(payload, dict) and payload:
        event = dict(payload)
    else:
        event = dict(item)
    if not event.get("log_id") and item.get("log_id"):
        event["log_id"] = item["log_id"]
    if not event.get("timestamp") and item.get("timestamp"):
        event["timestamp"] = item["timestamp"]
    return event


def _scan_error(message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "triggered_count": 0,
        "alert_ids": [],
        "report_ids": [],
        "error": message,
    }


def _coerce_str(value: Any) -> str:
    return "" if value is None else str(value)
