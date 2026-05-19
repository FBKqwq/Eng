from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from app.core.config import settings
from app.schemas.log import LogQueryRequest
from app.services.elasticsearch.client import get_es_client

ES_QUERY_TIMEOUT_SECONDS = 2


def search_logs(payload: LogQueryRequest) -> dict:
    """Search application logs in Elasticsearch and return a stable page payload."""
    query = _build_query(payload)
    page_from = (payload.page - 1) * payload.page_size
    sort = [{payload.sort_by: {"order": _enum_value(payload.sort_order), "unmapped_type": "keyword"}}]

    try:
        client = get_es_client().options(request_timeout=ES_QUERY_TIMEOUT_SECONDS, max_retries=0)
        response = client.search(
            index=settings.elasticsearch_index_pattern,
            query=query,
            from_=page_from,
            size=payload.page_size,
            sort=sort,
            track_total_hits=True,
            ignore_unavailable=True,
            allow_no_indices=True,
        )
        return _format_search_response(response, payload)
    except Exception as exc:  # noqa: BLE001 - API needs a stable diagnostic payload
        return {
            "available": False,
            "error": str(exc),
            "items": [],
            "total": 0,
            "page": payload.page,
            "page_size": payload.page_size,
            "has_more": False,
            "took_ms": None,
            "filters": _active_filters(payload),
        }


def search_recent_context(
    *,
    trace_id: str | None = None,
    service_name: str | None = None,
    error_code: str | None = None,
    limit: int = 20,
) -> dict:
    """Fetch a compact context page for diagnosis without exposing ES details."""
    payload = LogQueryRequest(
        trace_id=trace_id,
        service_names=[service_name] if service_name else None,
        error_codes=[error_code] if error_code else None,
        page=1,
        page_size=max(1, min(limit, 100)),
    )
    return search_logs(payload)


def _build_query(payload: LogQueryRequest) -> dict[str, Any]:
    must: list[dict[str, Any]] = []
    filters: list[dict[str, Any]] = []

    _add_terms(filters, "service_name", payload.service_names)
    _add_terms(filters, "log_level", payload.log_levels)
    _add_terms(filters, "log_type", payload.log_types)
    _add_terms(filters, "event_type", payload.event_types)
    _add_terms(filters, "error_code", payload.error_codes)
    _add_terms(filters, "status_code", payload.status_codes)
    _add_terms(filters, "status", payload.statuses)
    _add_terms(filters, "env", payload.envs)
    _add_terms(filters, "tags", payload.tags)
    _add_term(filters, "trace_id", payload.trace_id)
    _add_term(filters, "request_id", payload.request_id)
    _add_term(filters, "user_id", payload.user_id)
    _add_term(filters, "session_id", payload.session_id)
    _add_term(filters, "order_id", payload.order_id)

    time_range: dict[str, Any] = {}
    if payload.start_time:
        time_range["gte"] = _datetime_value(payload.start_time)
    if payload.end_time:
        time_range["lte"] = _datetime_value(payload.end_time)
    if time_range:
        filters.append({"range": {"timestamp": time_range}})

    if payload.keyword:
        must.append(
            {
                "multi_match": {
                    "query": payload.keyword,
                    "fields": [
                        "message^3",
                        "event_type",
                        "service_name",
                        "error_code",
                        "trace_id",
                        "request_path",
                        "event.original",
                    ],
                    "lenient": True,
                }
            }
        )

    if not must and not filters:
        return {"match_all": {}}
    return {"bool": {"must": must or [{"match_all": {}}], "filter": filters}}


def _format_search_response(response: Any, payload: LogQueryRequest) -> dict:
    data = _to_dict(response)
    hits_meta = data.get("hits") or {}
    total_meta = hits_meta.get("total", 0)
    total = int(total_meta.get("value", 0)) if isinstance(total_meta, dict) else int(total_meta or 0)
    hits = hits_meta.get("hits") or []
    items = [_hit_to_item(hit) for hit in hits]

    return {
        "available": True,
        "error": None,
        "items": items,
        "total": total,
        "page": payload.page,
        "page_size": payload.page_size,
        "has_more": payload.page * payload.page_size < total,
        "took_ms": data.get("took"),
        "filters": _active_filters(payload),
    }


def _hit_to_item(hit: Any) -> dict[str, Any]:
    hit_d = _to_dict(hit)
    source = hit_d.get("_source") or {}
    if not isinstance(source, dict):
        source = {}

    timestamp = source.get("timestamp") or source.get("@timestamp")
    payload = dict(source)
    return {
        "log_id": _coerce_str(source.get("log_id") or hit_d.get("_id")),
        "timestamp": timestamp,
        "log_level": source.get("log_level"),
        "log_type": source.get("log_type"),
        "event_type": source.get("event_type"),
        "service_name": source.get("service_name"),
        "message": source.get("message"),
        "trace_id": source.get("trace_id"),
        "request_id": source.get("request_id"),
        "user_id": source.get("user_id"),
        "status": source.get("status"),
        "summary": _build_summary(source),
        "payload": payload,
    }


def _add_terms(filters: list[dict[str, Any]], field: str, values: list[Any] | None) -> None:
    if values:
        cleaned = [_enum_value(v) for v in values if _enum_value(v) not in (None, "")]
        if cleaned:
            filters.append({"terms": {field: cleaned}})


def _add_term(filters: list[dict[str, Any]], field: str, value: Any) -> None:
    cleaned = _enum_value(value)
    if cleaned not in (None, ""):
        filters.append({"term": {field: cleaned}})


def _active_filters(payload: LogQueryRequest) -> dict[str, Any]:
    raw = payload.model_dump()
    return {k: _jsonable(v) for k, v in raw.items() if v not in (None, "", [], {})}


def _jsonable(value: Any) -> Any:
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, datetime):
        return _datetime_value(value)
    return _enum_value(value)


def _enum_value(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else value


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


def _build_summary(source: dict[str, Any]) -> str:
    service = source.get("service_name") or "unknown-service"
    level = source.get("log_level") or "UNKNOWN"
    message = source.get("message") or ""
    return f"[{level}] {service}: {message}"
