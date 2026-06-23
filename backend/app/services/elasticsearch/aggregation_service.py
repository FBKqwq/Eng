"""受控聚合查询服务。

职责：基于 LogAggregateRequest 组装 DSL，提供六类预置聚合模板。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from app.schemas.log import LogAggregateRequest, LogType, TimeInterval
from app.services.elasticsearch.client import get_es_client
from app.services.elasticsearch.field_catalog import (
    FIELD_CATALOG,
    resolve_index_pattern,
    validate_aggregate_request,
)

ES_QUERY_TIMEOUT_SECONDS = 2
MAX_TOP_N = 50
MAX_WINDOW_HOURS = 24
_NUMERIC_TERMS_FIELDS = frozenset({"status_code"})
# 索引模板中以 text + keyword 多字段方式映射的字段（见 index_service._text_with_keyword）。
# 仅这些字段做 terms 聚合时需要 .keyword 子字段；其余枚举字段本身即 keyword，直接聚合。
_TEXT_MULTIFIELD_TERMS = frozenset({"message", "reason", "change_summary"})


def aggregate(request: LogAggregateRequest) -> dict[str, Any]:
    """统一聚合入口：校验 field_catalog 后组装 DSL 并执行。"""
    group_by = _enum_value(request.group_by)
    interval = _enum_value(request.interval)
    top_n = _cap_top_n(request.top_n)

    window_error = _validate_time_window(request.start_time, request.end_time)
    if window_error:
        return _error_response(group_by, interval, window_error)

    log_type_strs = _log_types_to_strings(request.log_types)
    validation = validate_aggregate_request(log_type_strs, group_by)
    if not validation["ok"]:
        return _error_response(group_by, interval, "; ".join(validation["errors"]))

    index = _resolve_search_index(log_type_strs)
    query = _build_base_query(
        start_time=request.start_time,
        end_time=request.end_time,
        log_types=log_type_strs,
        service_names=request.service_names,
        extra_filters=request.filters,
    )
    aggs = _build_group_by_aggs(group_by=group_by, top_n=top_n, interval=interval)
    body = {"size": 0, "query": query, "aggs": aggs}

    return _execute_and_format(
        index=index,
        body=body,
        group_by=group_by,
        interval=interval,
        bucket_parser=lambda data: _parse_group_by_buckets(data, interval),
    )


def aggregate_traffic(
    *,
    start_time: datetime,
    end_time: datetime,
    interval: TimeInterval | str = TimeInterval.minute,
    top_n: int = 10,
    service_names: list[str] | None = None,
    **_: Any,
) -> dict[str, Any]:
    """流量统计：application + web_server，按时间直方图计数。"""
    interval_val = _enum_value(interval) or TimeInterval.minute.value
    log_types = [LogType.application.value, LogType.web_server.value]
    window_error = _validate_time_window(start_time, end_time)
    if window_error:
        return _error_response("timestamp", interval_val, window_error)

    index = _resolve_search_index(log_types)
    query = _build_base_query(
        start_time=start_time,
        end_time=end_time,
        log_types=log_types,
        service_names=service_names,
    )
    body = {
        "size": 0,
        "query": query,
        "aggs": {
            "traffic_over_time": {
                "date_histogram": {
                    "field": "timestamp",
                    "fixed_interval": interval_val,
                    "min_doc_count": 0,
                }
            },
            "by_service": {
                "terms": {"field": _terms_field("service_name"), "size": _cap_top_n(top_n)},
            },
        },
    }
    return _execute_and_format(
        index=index,
        body=body,
        group_by="timestamp",
        interval=interval_val,
        bucket_parser=_parse_traffic_buckets,
    )


def aggregate_errors(
    *,
    start_time: datetime,
    end_time: datetime,
    top_n: int = 10,
    service_names: list[str] | None = None,
    interval: TimeInterval | str | None = None,
    **_: Any,
) -> dict[str, Any]:
    """错误统计：错误过滤 + error_code / status_code 分布；带 interval 时返回错误量时间直方图。"""
    log_types = [LogType.application.value, LogType.web_server.value]
    window_error = _validate_time_window(start_time, end_time)
    if window_error:
        return _error_response("error_code", None, window_error)

    capped = _cap_top_n(top_n)
    index = _resolve_search_index(log_types)
    base_query = _build_base_query(
        start_time=start_time,
        end_time=end_time,
        log_types=log_types,
        service_names=service_names,
    )
    query = {
        "bool": {
            "filter": base_query["bool"]["filter"],
            "should": [
                {"term": {"log_level": "ERROR"}},
                {"range": {"status_code": {"gte": 400}}},
            ],
            "minimum_should_match": 1,
        }
    }

    if interval:
        interval_val = _enum_value(interval) or TimeInterval.minute.value
        body = {
            "size": 0,
            "query": query,
            "aggs": {
                "errors_over_time": {
                    "date_histogram": {
                        "field": "timestamp",
                        "fixed_interval": interval_val,
                        "min_doc_count": 0,
                    }
                }
            },
        }
        return _execute_and_format(
            index=index,
            body=body,
            group_by="timestamp",
            interval=interval_val,
            bucket_parser=lambda data: _parse_time_histogram_buckets(data, "errors_over_time"),
        )

    body = {
        "size": 0,
        "query": query,
        "aggs": {
            "by_error_code": {"terms": {"field": _terms_field("error_code"), "size": capped}},
            "by_status_code": {"terms": {"field": "status_code", "size": capped}},
            "by_service": {"terms": {"field": _terms_field("service_name"), "size": capped}},
        },
    }
    return _execute_and_format(
        index=index,
        body=body,
        group_by="error_code",
        interval=None,
        bucket_parser=_parse_errors_buckets,
    )


def aggregate_by_template(request: LogAggregateRequest) -> dict[str, Any]:
    """按预置模板路由聚合，供 REST API 与 Agent 工具共用。"""
    template = _enum_value(request.template)
    dispatch: dict[str, Any] = {
        "traffic": aggregate_traffic,
        "errors": aggregate_errors,
        "latency": aggregate_latency,
        "behavior_funnel": aggregate_behavior_funnel,
        "security": aggregate_security,
        "infra_health": aggregate_infra_health,
    }
    handler = dispatch.get(template or "")
    if handler is None:
        return _error_response("template", None, f"未知的聚合模板: {template}")

    capped = _cap_top_n(request.top_n)
    service_names = request.service_names
    start_time = request.start_time
    end_time = request.end_time
    interval = request.interval

    if template == "traffic":
        return handler(
            start_time=start_time,
            end_time=end_time,
            interval=interval or TimeInterval.minute,
            top_n=capped,
            service_names=service_names,
        )
    if template == "errors":
        return handler(
            start_time=start_time,
            end_time=end_time,
            top_n=capped,
            service_names=service_names,
            interval=interval,
        )
    if template == "behavior_funnel":
        return handler(start_time=start_time, end_time=end_time)
    return handler(
        start_time=start_time,
        end_time=end_time,
        top_n=capped,
        service_names=service_names,
    )


def aggregate_latency(
    *,
    start_time: datetime,
    end_time: datetime,
    top_n: int = 10,
    service_names: list[str] | None = None,
    **_: Any,
) -> dict[str, Any]:
    """耗时统计：全局与各服务 p50/p95/p99。"""
    log_types = [
        LogType.application.value,
        LogType.web_server.value,
        LogType.performance.value,
    ]
    window_error = _validate_time_window(start_time, end_time)
    if window_error:
        return _error_response("service_name", None, window_error)

    capped = _cap_top_n(top_n)
    index = _resolve_search_index(log_types)
    query = _build_base_query(
        start_time=start_time,
        end_time=end_time,
        log_types=log_types,
        service_names=service_names,
    )
    body = {
        "size": 0,
        "query": query,
        "aggs": {
            "global_latency": {
                "percentiles": {
                    "field": "response_time_ms",
                    "percents": [50, 95, 99],
                }
            },
            "by_service": {
                "terms": {"field": _terms_field("service_name"), "size": capped},
                "aggs": {
                    "latency_percentiles": {
                        "percentiles": {
                            "field": "response_time_ms",
                            "percents": [50, 95, 99],
                        }
                    }
                },
            },
        },
    }
    return _execute_and_format(
        index=index,
        body=body,
        group_by="service_name",
        interval=None,
        bucket_parser=_parse_latency_buckets,
    )


def aggregate_behavior_funnel(
    *,
    start_time: datetime,
    end_time: datetime,
    **_: Any,
) -> dict[str, Any]:
    """行为漏斗：按 funnel_steps 逐步计数与转化率。"""
    log_types = [LogType.behavior.value]
    funnel_steps: list[str] = FIELD_CATALOG["behavior"].get("funnel_steps", [])
    window_error = _validate_time_window(start_time, end_time)
    if window_error:
        return _error_response("event_type", None, window_error)

    index = _resolve_search_index(log_types)
    query = _build_base_query(
        start_time=start_time,
        end_time=end_time,
        log_types=log_types,
    )
    step_aggs = {
        f"step_{step}": {"filter": {"term": {"event_type": step}}}
        for step in funnel_steps
    }
    body = {"size": 0, "query": query, "aggs": step_aggs}
    return _execute_and_format(
        index=index,
        body=body,
        group_by="event_type",
        interval=None,
        bucket_parser=lambda data: _parse_funnel_buckets(data, funnel_steps),
    )


def aggregate_security(
    *,
    start_time: datetime,
    end_time: datetime,
    top_n: int = 10,
    service_names: list[str] | None = None,
    **_: Any,
) -> dict[str, Any]:
    """安全统计：risk_level 分布与拦截次数。"""
    log_types = [LogType.security.value]
    window_error = _validate_time_window(start_time, end_time)
    if window_error:
        return _error_response("risk_level", None, window_error)

    capped = _cap_top_n(top_n)
    index = _resolve_search_index(log_types)
    query = _build_base_query(
        start_time=start_time,
        end_time=end_time,
        log_types=log_types,
        service_names=service_names,
    )
    body = {
        "size": 0,
        "query": query,
        "aggs": {
            "by_risk_level": {"terms": {"field": _terms_field("risk_level"), "size": capped}},
            "blocked_count": {
                "filter": {
                    "bool": {
                        "should": [
                            {"term": {"is_blocked": True}},
                            {"term": {"status_code": 403}},
                        ],
                        "minimum_should_match": 1,
                    }
                }
            },
            "by_client_ip": {"terms": {"field": _terms_field("client_ip"), "size": capped}},
        },
    }
    return _execute_and_format(
        index=index,
        body=body,
        group_by="risk_level",
        interval=None,
        bucket_parser=_parse_security_buckets,
    )


def aggregate_infra_health(
    *,
    start_time: datetime,
    end_time: datetime,
    top_n: int = 10,
    metric_field: str = "cpu_percent",
    **_: Any,
) -> dict[str, Any]:
    """基础设施健康：按 component 分组并计算指标均值。"""
    log_types = [LogType.infrastructure.value, LogType.performance.value]
    window_error = _validate_time_window(start_time, end_time)
    if window_error:
        return _error_response("component", None, window_error)

    validation = validate_aggregate_request(
        [LogType.infrastructure.value],
        "component",
        metric_field=metric_field,
    )
    if not validation["ok"]:
        return _error_response("component", None, "; ".join(validation["errors"]))

    capped = _cap_top_n(top_n)
    index = _resolve_search_index(log_types)
    query = _build_base_query(
        start_time=start_time,
        end_time=end_time,
        log_types=log_types,
    )
    body = {
        "size": 0,
        "query": query,
        "aggs": {
            "by_component": {
                "terms": {"field": _terms_field("component"), "size": capped},
                "aggs": {
                    "avg_metric": {"avg": {"field": metric_field}},
                },
            },
            "avg_metric_global": {"avg": {"field": metric_field}},
        },
    }
    return _execute_and_format(
        index=index,
        body=body,
        group_by="component",
        interval=None,
        bucket_parser=lambda data: _parse_infra_buckets(data, metric_field),
    )


def _execute_and_format(
    *,
    index: str,
    body: dict[str, Any],
    group_by: str,
    interval: str | None,
    bucket_parser: Any,
) -> dict[str, Any]:
    try:
        client = get_es_client().options(request_timeout=ES_QUERY_TIMEOUT_SECONDS, max_retries=0)
        response = client.search(
            index=index,
            query=body["query"],
            size=0,
            aggs=body["aggs"],
            ignore_unavailable=True,
            allow_no_indices=True,
        )
        data = _to_dict(response)
        buckets, extra = bucket_parser(data.get("aggregations") or {})
        result = _success_response(group_by, interval, buckets, data.get("took"))
        if extra:
            result["extra"] = extra
        return result
    except Exception as exc:  # noqa: BLE001 - 与 log_query_service 保持一致的稳定错误载荷
        return _error_response(group_by, interval, str(exc))


def _build_group_by_aggs(
    *,
    group_by: str,
    top_n: int,
    interval: str | None,
) -> dict[str, Any]:
    terms_agg = {"terms": {"field": _terms_field(group_by), "size": top_n}}
    if interval:
        return {
            "time_buckets": {
                "date_histogram": {
                    "field": "timestamp",
                    "fixed_interval": interval,
                    "min_doc_count": 0,
                },
                "aggs": {"by_group": terms_agg},
            }
        }
    return {"by_group": terms_agg}


def _build_base_query(
    *,
    start_time: datetime,
    end_time: datetime,
    log_types: list[str] | None = None,
    service_names: list[str] | None = None,
    extra_filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    filters: list[dict[str, Any]] = [
        {
            "range": {
                "timestamp": {
                    "gte": _datetime_value(start_time),
                    "lte": _datetime_value(end_time),
                }
            }
        }
    ]
    if log_types:
        filters.append({"terms": {"log_type": log_types}})
    if service_names:
        filters.append({"terms": {"service_name": service_names}})
    if extra_filters:
        for field, value in extra_filters.items():
            if value in (None, "", [], {}):
                continue
            if isinstance(value, list):
                filters.append({"terms": {field: [_enum_value(v) for v in value]}})
            else:
                filters.append({"term": {field: _enum_value(value)}})
    return {"bool": {"filter": filters}}


def _resolve_search_index(log_types: list[str] | None) -> str:
    """解析 ES 索引 pattern，与 Logstash / index_service 按 log_type 拆分写入对齐。"""
    return resolve_index_pattern(log_types)


def _terms_field(field: str) -> str:
    """解析 terms 聚合的实际字段名。

    索引模板将绝大多数枚举字段直接映射为 keyword（无 .keyword 子字段），
    只有少数自由文本字段（message/reason/change_summary）才是 text + keyword 多字段。
    因此默认原样返回字段名，仅对多字段文本补 .keyword，避免聚合静默命中不存在的字段。
    """
    if field.endswith(".keyword") or field in _NUMERIC_TERMS_FIELDS:
        return field
    if field in _TEXT_MULTIFIELD_TERMS:
        return f"{field}.keyword"
    return field


def _validate_time_window(start_time: datetime, end_time: datetime) -> str | None:
    if end_time <= start_time:
        return "end_time 必须大于 start_time"
    if end_time - start_time > timedelta(hours=MAX_WINDOW_HOURS):
        return f"时间窗口跨度不能超过 {MAX_WINDOW_HOURS} 小时"
    return None


def _cap_top_n(top_n: int) -> int:
    return max(1, min(top_n, MAX_TOP_N))


def _log_types_to_strings(log_types: list[LogType] | None) -> list[str] | None:
    if not log_types:
        return None
    return [_enum_value(lt) for lt in log_types]


def _success_response(
    group_by: str,
    interval: str | None,
    buckets: list[dict[str, Any]],
    took_ms: int | None,
) -> dict[str, Any]:
    return {
        "available": True,
        "error": None,
        "group_by": group_by,
        "interval": interval,
        "buckets": buckets,
        "took_ms": took_ms,
    }


def _error_response(group_by: str, interval: str | None, error: str) -> dict[str, Any]:
    return {
        "available": False,
        "error": error,
        "group_by": group_by,
        "interval": interval,
        "buckets": [],
        "took_ms": None,
    }


def _parse_group_by_buckets(
    aggs: dict[str, Any],
    interval: str | None,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    if interval:
        buckets: list[dict[str, Any]] = []
        for bucket in aggs.get("time_buckets", {}).get("buckets", []):
            key = _format_bucket_key(bucket.get("key_as_string") or bucket.get("key"))
            sub_buckets = _terms_to_buckets(bucket.get("by_group", {}).get("buckets", []))
            buckets.append(
                {
                    "key": key,
                    "count": int(bucket.get("doc_count", 0)),
                    "extra": {"sub_buckets": sub_buckets} if sub_buckets else None,
                }
            )
        return buckets, None

    return _terms_to_buckets(aggs.get("by_group", {}).get("buckets", [])), None


def _parse_traffic_buckets(aggs: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    buckets, _ = _parse_time_histogram_buckets(aggs, "traffic_over_time")
    by_service = _terms_to_buckets(aggs.get("by_service", {}).get("buckets", []))
    extra = {"by_service": by_service, "total_count": sum(b["count"] for b in buckets)}
    return buckets, extra


def _parse_time_histogram_buckets(
    aggs: dict[str, Any],
    agg_name: str,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    buckets: list[dict[str, Any]] = []
    for bucket in aggs.get(agg_name, {}).get("buckets", []):
        buckets.append(
            {
                "key": _format_bucket_key(bucket.get("key_as_string") or bucket.get("key")),
                "count": int(bucket.get("doc_count", 0)),
            }
        )
    return buckets, None


def _parse_errors_buckets(aggs: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    buckets = _terms_to_buckets(aggs.get("by_error_code", {}).get("buckets", []))
    extra = {
        "by_status_code": _terms_to_buckets(aggs.get("by_status_code", {}).get("buckets", [])),
        "by_service": _terms_to_buckets(aggs.get("by_service", {}).get("buckets", [])),
    }
    return buckets, extra


def _parse_latency_buckets(aggs: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    global_pct = _parse_percentiles(aggs.get("global_latency", {}))
    buckets: list[dict[str, Any]] = []
    for bucket in aggs.get("by_service", {}).get("buckets", []):
        pct = _parse_percentiles(bucket.get("latency_percentiles", {}))
        buckets.append(
            {
                "key": _format_bucket_key(bucket.get("key")),
                "count": int(bucket.get("doc_count", 0)),
                "extra": pct,
            }
        )
    return buckets, {"global_percentiles": global_pct}


def _parse_funnel_buckets(
    aggs: dict[str, Any],
    funnel_steps: list[str],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    buckets: list[dict[str, Any]] = []
    prev_count: int | None = None
    for step in funnel_steps:
        count = int(aggs.get(f"step_{step}", {}).get("doc_count", 0))
        conversion_rate = None
        if prev_count is not None and prev_count > 0:
            conversion_rate = round(count / prev_count, 4)
        buckets.append(
            {
                "key": step,
                "count": count,
                "extra": {"conversion_rate": conversion_rate},
            }
        )
        prev_count = count
    return buckets, {"funnel_steps": funnel_steps}


def _parse_security_buckets(aggs: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    buckets = _terms_to_buckets(aggs.get("by_risk_level", {}).get("buckets", []))
    extra = {
        "blocked_count": int(aggs.get("blocked_count", {}).get("doc_count", 0)),
        "by_client_ip": _terms_to_buckets(aggs.get("by_client_ip", {}).get("buckets", [])),
    }
    return buckets, extra


def _parse_infra_buckets(
    aggs: dict[str, Any],
    metric_field: str,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    buckets: list[dict[str, Any]] = []
    for bucket in aggs.get("by_component", {}).get("buckets", []):
        avg_val = bucket.get("avg_metric", {}).get("value")
        buckets.append(
            {
                "key": _format_bucket_key(bucket.get("key")),
                "count": int(bucket.get("doc_count", 0)),
                "value": avg_val,
                "extra": {"metric_field": metric_field},
            }
        )
    global_avg = aggs.get("avg_metric_global", {}).get("value")
    return buckets, {"avg_metric_global": global_avg, "metric_field": metric_field}


def _terms_to_buckets(raw_buckets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: list[dict[str, Any]] = []
    for bucket in raw_buckets:
        key = bucket.get("key")
        if key in (None, ""):
            continue
        buckets.append(
            {
                "key": _format_bucket_key(key),
                "count": int(bucket.get("doc_count", 0)),
            }
        )
    return buckets


def _parse_percentiles(agg: dict[str, Any]) -> dict[str, float | None]:
    values = agg.get("values", {})
    return {
        "p50": values.get("50.0"),
        "p95": values.get("95.0"),
        "p99": values.get("99.0"),
    }


def _format_bucket_key(key: Any) -> str:
    if key is None:
        return ""
    return str(key)


def _enum_value(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else value


def _datetime_value(value: datetime) -> str:
    return value.isoformat()


def _to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "body"):
        body = value.body
        return body if isinstance(body, dict) else dict(body)
    if hasattr(value, "to_dict"):
        return value.to_dict()
    try:
        return dict(value)
    except Exception:
        return {}
