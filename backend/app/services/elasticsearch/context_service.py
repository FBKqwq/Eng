"""诊断上下文查询服务。

职责：为规则子图提供 trace/服务窗口/同类错误/用户行为四类受控上下文入口。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §1.2.4

说明：本模块独立实现受控上下文查询；诊断模块未来应迁移至本 service，
而非继续扩展 log_query_service.search_recent_context（该函数本任务不得改动）。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.services.elasticsearch.client import get_es_client
from app.services.elasticsearch.field_catalog import resolve_index_pattern

CONTEXT_QUERY_TIMEOUT_SECONDS = 2
MAX_LIMIT = 50
MAX_WINDOW_HOURS = 24

_LEVEL_PRIORITY = {"ERROR": 0, "WARN": 1, "WARNING": 1}


def get_trace_context(trace_id: str, *, limit: int = 50) -> dict[str, Any]:
    """跨索引查同 trace 日志，按 timestamp 升序。"""
    effective_limit = _clamp_limit(limit)
    cleaned_trace = (trace_id or "").strip()
    if not cleaned_trace:
        return _error_payload(items=[], total=0, error="trace_id 不能为空")

    query = {
        "bool": {
            "filter": [{"term": {"trace_id": cleaned_trace}}],
        }
    }
    sort = [{"timestamp": {"order": "asc", "unmapped_type": "date"}}]
    index_pattern = resolve_index_pattern(None)

    return _search_items(
        index_pattern=index_pattern,
        query=query,
        sort=sort,
        limit=effective_limit,
        extra={"trace_id": cleaned_trace},
    )


def get_service_window(
    service: str,
    start: datetime,
    end: datetime,
    *,
    limit: int = 50,
) -> dict[str, Any]:
    """查服务时间窗口内日志，ERROR/WARN 优先，并返回 level_distribution。"""
    effective_limit = _clamp_limit(limit)
    cleaned_service = (service or "").strip()
    window_error = _validate_time_window(start, end)
    if window_error:
        return _error_payload(
            items=[],
            total=0,
            error=window_error,
            service=cleaned_service,
            start=start.isoformat(),
            end=end.isoformat(),
            level_distribution={},
        )
    if not cleaned_service:
        return _error_payload(
            items=[],
            total=0,
            error="service 不能为空",
            service=cleaned_service,
            start=start.isoformat(),
            end=end.isoformat(),
            level_distribution={},
        )

    query = _build_bool_filter_query(
        [
            {"term": {"service_name": cleaned_service}},
            _time_range_filter(start, end),
        ]
    )
    sort = _level_priority_sort() + [{"timestamp": {"order": "desc", "unmapped_type": "date"}}]
    index_pattern = resolve_index_pattern(None)

    try:
        client = get_es_client().options(
            request_timeout=CONTEXT_QUERY_TIMEOUT_SECONDS,
            max_retries=0,
        )
        response = client.search(
            index=index_pattern,
            query=query,
            size=effective_limit,
            sort=sort,
            track_total_hits=True,
            ignore_unavailable=True,
            allow_no_indices=True,
            aggs={
                "level_distribution": {
                    "terms": {"field": "log_level", "size": 20},
                }
            },
        )
        data = _to_dict(response)
        hits_meta = data.get("hits") or {}
        total_meta = hits_meta.get("total", 0)
        total = int(total_meta.get("value", 0)) if isinstance(total_meta, dict) else int(total_meta or 0)
        hits = hits_meta.get("hits") or []
        items = [_hit_to_item(hit) for hit in hits]
        level_distribution = _terms_agg_to_dict(
            ((data.get("aggregations") or {}).get("level_distribution") or {})
        )

        return {
            "available": True,
            "error": None,
            "items": items,
            "total": total,
            "took_ms": data.get("took"),
            "service": cleaned_service,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "level_distribution": level_distribution,
        }
    except Exception as exc:  # noqa: BLE001 - 返回稳定诊断载荷，不抛到 API
        return _error_payload(
            items=[],
            total=0,
            error=str(exc),
            service=cleaned_service,
            start=start.isoformat(),
            end=end.isoformat(),
            level_distribution={},
        )


def get_similar_errors(
    error_code: str,
    start: datetime,
    end: datetime,
    *,
    limit: int = 50,
) -> dict[str, Any]:
    """查同类错误分布，判断集中爆发。"""
    effective_limit = _clamp_limit(limit)
    cleaned_code = (error_code or "").strip()
    window_error = _validate_time_window(start, end)
    if window_error:
        return _error_payload(
            items=[],
            total=0,
            error=window_error,
            error_code=cleaned_code,
            start=start.isoformat(),
            end=end.isoformat(),
            by_service=[],
            time_histogram=[],
        )
    if not cleaned_code:
        return _error_payload(
            items=[],
            total=0,
            error="error_code 不能为空",
            error_code=cleaned_code,
            start=start.isoformat(),
            end=end.isoformat(),
            by_service=[],
            time_histogram=[],
        )

    query = _build_bool_filter_query(
        [
            {"term": {"error_code": cleaned_code}},
            _time_range_filter(start, end),
        ]
    )
    histogram_interval = _histogram_interval(start, end)
    index_pattern = resolve_index_pattern(None)

    try:
        client = get_es_client().options(
            request_timeout=CONTEXT_QUERY_TIMEOUT_SECONDS,
            max_retries=0,
        )
        response = client.search(
            index=index_pattern,
            query=query,
            size=min(effective_limit, 10),
            sort=[{"timestamp": {"order": "desc", "unmapped_type": "date"}}],
            track_total_hits=True,
            ignore_unavailable=True,
            allow_no_indices=True,
            aggs={
                "by_service": {
                    "terms": {"field": "service_name", "size": 50},
                },
                "time_histogram": {
                    "date_histogram": {
                        "field": "timestamp",
                        "fixed_interval": histogram_interval,
                        "min_doc_count": 0,
                        "extended_bounds": {
                            "min": _datetime_value(start),
                            "max": _datetime_value(end),
                        },
                    }
                },
            },
        )
        data = _to_dict(response)
        hits_meta = data.get("hits") or {}
        total_meta = hits_meta.get("total", 0)
        total = int(total_meta.get("value", 0)) if isinstance(total_meta, dict) else int(total_meta or 0)
        aggs = data.get("aggregations") or {}

        return {
            "available": True,
            "error": None,
            "total": total,
            "took_ms": data.get("took"),
            "error_code": cleaned_code,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "by_service": _terms_agg_to_buckets(aggs.get("by_service") or {}),
            "time_histogram": _date_histogram_to_buckets(aggs.get("time_histogram") or {}),
        }
    except Exception as exc:  # noqa: BLE001
        return _error_payload(
            items=[],
            total=0,
            error=str(exc),
            error_code=cleaned_code,
            start=start.isoformat(),
            end=end.isoformat(),
            by_service=[],
            time_histogram=[],
        )


def get_user_recent_actions(
    user_id: str,
    start: datetime,
    end: datetime,
    *,
    limit: int = 50,
) -> dict[str, Any]:
    """查 behavior + application 中用户行为序列，按时间升序。"""
    effective_limit = _clamp_limit(limit)
    cleaned_user = (user_id or "").strip()
    window_error = _validate_time_window(start, end)
    if window_error:
        return _error_payload(
            items=[],
            total=0,
            error=window_error,
            user_id=cleaned_user,
            start=start.isoformat(),
            end=end.isoformat(),
        )
    if not cleaned_user:
        return _error_payload(
            items=[],
            total=0,
            error="user_id 不能为空",
            user_id=cleaned_user,
            start=start.isoformat(),
            end=end.isoformat(),
        )

    query = _build_bool_filter_query(
        [
            {"term": {"user_id": cleaned_user}},
            _time_range_filter(start, end),
        ]
    )
    sort = [{"timestamp": {"order": "asc", "unmapped_type": "date"}}]
    index_pattern = resolve_index_pattern(["behavior", "application"])

    return _search_items(
        index_pattern=index_pattern,
        query=query,
        sort=sort,
        limit=effective_limit,
        extra={
            "user_id": cleaned_user,
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
    )


def _search_items(
    *,
    index_pattern: str,
    query: dict[str, Any],
    sort: list[dict[str, Any]],
    limit: int,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        client = get_es_client().options(
            request_timeout=CONTEXT_QUERY_TIMEOUT_SECONDS,
            max_retries=0,
        )
        response = client.search(
            index=index_pattern,
            query=query,
            size=limit,
            sort=sort,
            track_total_hits=True,
            ignore_unavailable=True,
            allow_no_indices=True,
        )
        data = _to_dict(response)
        hits_meta = data.get("hits") or {}
        total_meta = hits_meta.get("total", 0)
        total = int(total_meta.get("value", 0)) if isinstance(total_meta, dict) else int(total_meta or 0)
        hits = hits_meta.get("hits") or []
        items = [_hit_to_item(hit) for hit in hits]

        payload: dict[str, Any] = {
            "available": True,
            "error": None,
            "items": items,
            "total": total,
            "took_ms": data.get("took"),
        }
        if extra:
            payload.update(extra)
        return payload
    except Exception as exc:  # noqa: BLE001
        payload = _error_payload(items=[], total=0, error=str(exc))
        if extra:
            payload.update(extra)
        return payload


def _error_payload(*, items: list[Any], total: int, error: str, **extra: Any) -> dict[str, Any]:
    return {
        "available": False,
        "error": error,
        "items": items,
        "total": total,
        "took_ms": None,
        **extra,
    }


def _clamp_limit(limit: int) -> int:
    return max(1, min(int(limit), MAX_LIMIT))


def _validate_time_window(start: datetime, end: datetime) -> str | None:
    if end < start:
        return "end 必须大于等于 start"
    if end - start > timedelta(hours=MAX_WINDOW_HOURS):
        return f"时间窗口不能超过 {MAX_WINDOW_HOURS} 小时"
    return None


def _build_bool_filter_query(filters: list[dict[str, Any]]) -> dict[str, Any]:
    cleaned = [f for f in filters if f]
    if not cleaned:
        return {"match_all": {}}
    return {"bool": {"filter": cleaned}}


def _time_range_filter(start: datetime, end: datetime) -> dict[str, Any]:
    return {
        "range": {
            "timestamp": {
                "gte": _datetime_value(start),
                "lte": _datetime_value(end),
            }
        }
    }


def _level_priority_sort() -> list[dict[str, Any]]:
    """ERROR/WARN 优先排序脚本。"""
    return [
        {
            "_script": {
                "type": "number",
                "order": "asc",
                "script": {
                    "lang": "painless",
                    "source": (
                        "if (doc.containsKey('log_level.keyword') && doc['log_level.keyword'].size() > 0) { "
                        "  def lvl = doc['log_level.keyword'].value; "
                        "  if (lvl == 'ERROR') return 0; "
                        "  if (lvl == 'WARN' || lvl == 'WARNING') return 1; "
                        "  return 2; "
                        "} "
                        "if (doc.containsKey('log_level') && doc['log_level'].size() > 0) { "
                        "  def lvl = doc['log_level'].value; "
                        "  if (lvl == 'ERROR') return 0; "
                        "  if (lvl == 'WARN' || lvl == 'WARNING') return 1; "
                        "} "
                        "return 2;"
                    ),
                },
            }
        }
    ]


def _histogram_interval(start: datetime, end: datetime) -> str:
    span_hours = max((end - start).total_seconds() / 3600, 1 / 60)
    if span_hours <= 1:
        return "5m"
    if span_hours <= 6:
        return "15m"
    if span_hours <= 12:
        return "30m"
    return "1h"


def _terms_agg_to_dict(agg: dict[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    for bucket in agg.get("buckets") or []:
        key = bucket.get("key")
        if key is None:
            continue
        result[str(key)] = int(bucket.get("doc_count", 0))
    return result


def _terms_agg_to_buckets(agg: dict[str, Any]) -> list[dict[str, Any]]:
    buckets: list[dict[str, Any]] = []
    for bucket in agg.get("buckets") or []:
        key = bucket.get("key")
        if key is None:
            continue
        buckets.append({"key": str(key), "count": int(bucket.get("doc_count", 0))})
    buckets.sort(key=lambda item: item["count"], reverse=True)
    return buckets


def _date_histogram_to_buckets(agg: dict[str, Any]) -> list[dict[str, Any]]:
    buckets: list[dict[str, Any]] = []
    for bucket in agg.get("buckets") or []:
        key = bucket.get("key_as_string") or bucket.get("key")
        if key is None:
            continue
        buckets.append({"key": str(key), "count": int(bucket.get("doc_count", 0))})
    return buckets


def _hit_to_item(hit: Any) -> dict[str, Any]:
    """与 log_query_service 的 item 字段尽量一致。"""
    hit_d = _to_dict(hit)
    source = hit_d.get("_source") or {}
    if not isinstance(source, dict):
        source = {}

    timestamp = source.get("timestamp") or source.get("@timestamp")
    payload = dict(source)
    service = source.get("service_name") or "unknown-service"
    level = source.get("log_level") or "UNKNOWN"
    message = source.get("message") or ""
    return {
        "log_id": _coerce_str(source.get("log_id") or hit_d.get("_id")),
        "timestamp": timestamp,
        "log_level": source.get("log_level"),
        "log_type": source.get("log_type"),
        "event_type": source.get("event_type"),
        "service_name": source.get("service_name"),
        "message": source.get("message"),
        "error_code": source.get("error_code"),
        "trace_id": source.get("trace_id"),
        "request_id": source.get("request_id"),
        "user_id": source.get("user_id"),
        "status": source.get("status"),
        "summary": f"[{level}] {service}: {message}",
        "payload": payload,
    }


def _datetime_value(value: datetime) -> str:
    return value.isoformat()


def _to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    try:
        return dict(value)
    except Exception:
        return {}


def _coerce_str(value: Any) -> str:
    return "" if value is None else str(value)
