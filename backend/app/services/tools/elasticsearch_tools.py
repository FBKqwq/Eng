"""Elasticsearch 相关 Agent 工具。

包装：log_query_service / aggregation_service / context_service。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §3.2 工具 1-5、11-13
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


class EsGetBusinessFunnelInput(BaseModel):
    start_time: datetime
    end_time: datetime
    log_types: Optional[list[LogType]] = None
    top_n: int = Field(default=10, le=50)


class EsDetectTrafficPeakInput(BaseModel):
    start_time: datetime
    end_time: datetime
    interval: Optional[TimeInterval] = None
    group_by: Optional[str] = None
    top_n: int = Field(default=10, le=50)


class EsCompareTimeWindowsInput(BaseModel):
    current_start: datetime
    current_end: datetime
    baseline_start: datetime
    baseline_end: datetime
    template: Literal["traffic", "errors", "latency", "behavior_funnel", "security", "infra_health"] = "traffic"
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


def _trim_buckets(result: dict[str, Any], top_n: int = MAX_LIMIT) -> dict[str, Any]:
    """裁剪聚合桶数量，满足 §3.3 硬上限。"""
    payload = dict(result)
    capped = _clamp_limit(top_n)
    buckets = list(payload.get("buckets") or [])
    if len(buckets) > capped:
        payload["buckets"] = buckets[:capped]
        payload["truncated"] = True

    extra = payload.get("extra")
    if isinstance(extra, dict):
        trimmed_extra = dict(extra)
        for key in ("by_service", "by_status_code", "by_client_ip", "sub_buckets"):
            sub = trimmed_extra.get(key)
            if isinstance(sub, list) and len(sub) > capped:
                trimmed_extra[key] = sub[:capped]
                payload["truncated"] = True
        payload["extra"] = trimmed_extra
    return payload


def _find_peak_bucket(buckets: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not buckets:
        return None
    peak = max(buckets, key=lambda item: int(item.get("count", 0)))
    return {"key": peak.get("key"), "count": int(peak.get("count", 0))}


def _extract_aggregate_total(result: dict[str, Any], template: str) -> int:
    extra = result.get("extra") or {}
    if template == "traffic" and extra.get("total_count") is not None:
        return int(extra["total_count"])

    buckets = result.get("buckets") or []
    if template == "behavior_funnel" and buckets:
        return int(buckets[0].get("count", 0))

    return sum(int(item.get("count", 0)) for item in buckets)


def _compute_period_comparison(current_total: int, baseline_total: int) -> dict[str, Any]:
    delta = current_total - baseline_total
    change_percent: float | None
    if baseline_total > 0:
        change_percent = round(delta / baseline_total * 100, 2)
    else:
        change_percent = None if current_total == 0 else None
    return {
        "current_total": current_total,
        "baseline_total": baseline_total,
        "delta": delta,
        "change_percent": change_percent,
    }


def _invoke_aggregate_template(
    template: str,
    *,
    start_time: datetime,
    end_time: datetime,
    interval: TimeInterval | None = None,
    top_n: int = 10,
) -> dict[str, Any]:
    handler = _AGGREGATE_DISPATCH.get(template)
    if handler is None:
        raise ValueError(f"未知的聚合模板: {template}")

    capped = _clamp_limit(top_n)
    if template == "traffic":
        return handler(
            start_time=start_time,
            end_time=end_time,
            interval=interval or TimeInterval.minute,
            top_n=capped,
        )
    if template == "behavior_funnel":
        return handler(start_time=start_time, end_time=end_time)
    return handler(start_time=start_time, end_time=end_time, top_n=capped)


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


def es_get_business_funnel(params: EsGetBusinessFunnelInput) -> dict[str, Any]:
    """工具 11：行为漏斗洞察（各环节转化/流失）。"""
    tool = "es_get_business_funnel"
    try:
        window_error = _validate_time_window(params.start_time, params.end_time)
        if window_error:
            return _tool_error(tool, window_error)

        result = aggregation_service.aggregate_behavior_funnel(
            start_time=params.start_time,
            end_time=params.end_time,
        )
        trimmed = _trim_buckets(result, top_n=params.top_n)
        return _wrap_service_result(trimmed, tool)
    except Exception as exc:  # noqa: BLE001
        return _tool_error(tool, str(exc))


def es_detect_traffic_peak(params: EsDetectTrafficPeakInput) -> dict[str, Any]:
    """工具 12：请求高峰定位（时间桶峰值识别）。"""
    tool = "es_detect_traffic_peak"
    try:
        window_error = _validate_time_window(params.start_time, params.end_time)
        if window_error:
            return _tool_error(tool, window_error)

        top_n = _clamp_limit(params.top_n)
        result = aggregation_service.aggregate_traffic(
            start_time=params.start_time,
            end_time=params.end_time,
            interval=params.interval or TimeInterval.minute,
            top_n=top_n,
        )
        trimmed = _trim_buckets(result, top_n=top_n)
        peak_bucket = _find_peak_bucket(list(trimmed.get("buckets") or []))
        payload = _wrap_service_result(trimmed, tool)
        payload["peak_bucket"] = peak_bucket
        if params.group_by:
            payload["group_by"] = params.group_by
        return payload
    except Exception as exc:  # noqa: BLE001
        return _tool_error(tool, str(exc))


def es_compare_time_windows(params: EsCompareTimeWindowsInput) -> dict[str, Any]:
    """工具 13：双窗口环比变化分析。"""
    tool = "es_compare_time_windows"
    try:
        for label, start, end in (
            ("current", params.current_start, params.current_end),
            ("baseline", params.baseline_start, params.baseline_end),
        ):
            window_error = _validate_time_window(start, end)
            if window_error:
                return _tool_error(tool, f"{label} 窗口: {window_error}")

        current_result = _invoke_aggregate_template(
            params.template,
            start_time=params.current_start,
            end_time=params.current_end,
            interval=params.interval,
            top_n=params.top_n,
        )
        baseline_result = _invoke_aggregate_template(
            params.template,
            start_time=params.baseline_start,
            end_time=params.baseline_end,
            interval=params.interval,
            top_n=params.top_n,
        )

        if not current_result.get("available") or current_result.get("error"):
            return _tool_error(
                tool,
                f"当前窗口聚合失败: {current_result.get('error') or '不可用'}",
            )
        if not baseline_result.get("available") or baseline_result.get("error"):
            return _tool_error(
                tool,
                f"对比窗口聚合失败: {baseline_result.get('error') or '不可用'}",
            )

        current_trimmed = _trim_buckets(current_result, top_n=params.top_n)
        baseline_trimmed = _trim_buckets(baseline_result, top_n=params.top_n)
        comparison = _compute_period_comparison(
            _extract_aggregate_total(current_trimmed, params.template),
            _extract_aggregate_total(baseline_trimmed, params.template),
        )

        return {
            "ok": True,
            "tool": tool,
            "template": params.template,
            "current_window": current_trimmed,
            "baseline_window": baseline_trimmed,
            "comparison": comparison,
        }
    except Exception as exc:  # noqa: BLE001
        return _tool_error(tool, str(exc))
