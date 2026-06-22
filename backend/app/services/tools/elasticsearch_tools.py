"""Elasticsearch 相关 Agent 工具。

包装：log_query_service / aggregation_service / context_service。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §3.2 工具 1-5
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.log import LogQueryRequest, LogType, TimeInterval
from app.services.elasticsearch import aggregation_service, context_service, log_query_service

MAX_LIMIT = 50
MAX_WINDOW_HOURS = 24

_AGGREGATE_DISPATCH = {
    "traffic": aggregation_service.aggregate_traffic,
    "errors": aggregation_service.aggregate_errors,
    "latency": aggregation_service.aggregate_latency,
    "behavior_funnel": aggregation_service.aggregate_behavior_funnel,
    "security": aggregation_service.aggregate_security,
    "infra_health": aggregation_service.aggregate_infra_health,
}


class EsSearchLogsInput(BaseModel):
    keyword: Optional[str] = None
    log_type: Optional[LogType] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=50, le=50)


class EsAggregateMetricsInput(BaseModel):
    template: Literal["traffic", "errors", "latency", "behavior_funnel", "security", "infra_health"]
    log_types: Optional[list[LogType]] = None
    start_time: datetime
    end_time: datetime
    interval: Optional[TimeInterval] = None
    top_n: int = Field(default=10, le=50)


def _validate_time_window(start_time: datetime, end_time: datetime) -> str | None:
    if end_time <= start_time:
        return "end_time 必须大于 start_time"
    if end_time - start_time > timedelta(hours=MAX_WINDOW_HOURS):
        return f"时间窗口跨度不能超过 {MAX_WINDOW_HOURS} 小时"
    return None


def _clamp_limit(value: int) -> int:
    return max(1, min(int(value), MAX_LIMIT))


def _tool_error(tool: str, error: str) -> dict[str, Any]:
    return {"ok": False, "error": error, "tool": tool}


def _wrap_service_result(result: dict[str, Any], tool: str) -> dict[str, Any]:
    payload = dict(result)
    payload["ok"] = bool(result.get("available")) and not result.get("error")
    payload["tool"] = tool
    return payload


def es_search_logs(params: EsSearchLogsInput) -> dict[str, Any]:
    """工具 1：搜索日志样本。"""
    tool = "es_search_logs"
    try:
        if params.start_time and params.end_time:
            window_error = _validate_time_window(params.start_time, params.end_time)
            if window_error:
                return _tool_error(tool, window_error)

        request = LogQueryRequest(
            keyword=params.keyword,
            log_types=[params.log_type] if params.log_type else None,
            start_time=params.start_time,
            end_time=params.end_time,
            page=1,
            page_size=_clamp_limit(params.limit),
        )
        result = log_query_service.search_logs(request)
        return _wrap_service_result(result, tool)
    except Exception as exc:  # noqa: BLE001 - 工具层统一错误载荷
        return _tool_error(tool, str(exc))


def es_aggregate_metrics(params: EsAggregateMetricsInput) -> dict[str, Any]:
    """工具 2：六模板聚合统一入口。"""
    tool = "es_aggregate_metrics"
    try:
        window_error = _validate_time_window(params.start_time, params.end_time)
        if window_error:
            return _tool_error(tool, window_error)

        handler = _AGGREGATE_DISPATCH.get(params.template)
        if handler is None:
            return _tool_error(tool, f"未知的聚合模板: {params.template}")

        top_n = _clamp_limit(params.top_n)
        start_time = params.start_time
        end_time = params.end_time

        if params.template == "traffic":
            result = handler(
                start_time=start_time,
                end_time=end_time,
                interval=params.interval or TimeInterval.minute,
                top_n=top_n,
            )
        elif params.template == "behavior_funnel":
            result = handler(start_time=start_time, end_time=end_time)
        else:
            result = handler(start_time=start_time, end_time=end_time, top_n=top_n)

        return _wrap_service_result(result, tool)
    except Exception as exc:  # noqa: BLE001
        return _tool_error(tool, str(exc))


def es_get_trace_context(trace_id: str, *, limit: int = 50) -> dict[str, Any]:
    """工具 3：trace 上下文。"""
    tool = "es_get_trace_context"
    try:
        result = context_service.get_trace_context(trace_id, limit=_clamp_limit(limit))
        return _wrap_service_result(result, tool)
    except Exception as exc:  # noqa: BLE001
        return _tool_error(tool, str(exc))


def es_get_service_window(service: str, start_time: datetime, end_time: datetime) -> dict[str, Any]:
    """工具 4：服务窗口上下文。"""
    tool = "es_get_service_window"
    try:
        window_error = _validate_time_window(start_time, end_time)
        if window_error:
            return _tool_error(tool, window_error)

        result = context_service.get_service_window(service, start_time, end_time)
        return _wrap_service_result(result, tool)
    except Exception as exc:  # noqa: BLE001
        return _tool_error(tool, str(exc))


def es_get_similar_errors(error_code: str, start_time: datetime, end_time: datetime) -> dict[str, Any]:
    """工具 5：同类错误分布。"""
    tool = "es_get_similar_errors"
    try:
        window_error = _validate_time_window(start_time, end_time)
        if window_error:
            return _tool_error(tool, window_error)

        result = context_service.get_similar_errors(error_code, start_time, end_time)
        return _wrap_service_result(result, tool)
    except Exception as exc:  # noqa: BLE001
        return _tool_error(tool, str(exc))
