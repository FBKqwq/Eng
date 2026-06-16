"""80+ 日志类型字段目录。

职责：声明每个 log_type 可筛选/聚合/指标字段，作为 aggregation、MCP 工具、前端筛选器的安全边界。
字段名与 schemas/log.py 及 simulation/log_generator.py 产出字段对齐。
"""

from __future__ import annotations

from typing import Any

# 七类日志公共可筛选字段（源自 LogBase）
_COMMON_FILTER_FIELDS: list[str] = [
    "timestamp",
    "log_id",
    "log_level",
    "log_type",
    "event_type",
    "service_name",
    "service_instance",
    "host",
    "env",
    "message",
    "source_type",
    "trace_id",
    "span_id",
    "request_id",
    "user_id",
    "session_id",
    "client_ip",
    "user_agent",
    "status",
    "tags",
]

_COMMON_TERMS_FIELDS: list[str] = [
    "log_level",
    "log_type",
    "event_type",
    "service_name",
    "service_instance",
    "host",
    "env",
    "source_type",
    "user_id",
    "session_id",
    "client_ip",
    "status",
]

_BEHAVIOR_FUNNEL_STEPS: list[str] = [
    "page_view",
    "product_click",
    "add_to_cart",
    "checkout_click",
    "pay_button_click",
]

FIELD_CATALOG: dict[str, dict[str, Any]] = {
    "behavior": {
        "filter_fields": _COMMON_FILTER_FIELDS
        + [
            "action",
            "page",
            "module",
            "product_id",
            "product_name",
            "category_id",
            "cart_id",
            "order_id",
            "payment_id",
            "recommendation_id",
            "strategy_id",
            "keyword",
            "result_count",
            "position",
            "quantity",
            "amount",
            "currency",
            "is_success",
            "response_time_ms",
            "status_code",
        ],
        "terms_fields": _COMMON_TERMS_FIELDS
        + [
            "action",
            "page",
            "module",
            "product_id",
            "product_name",
            "category_id",
            "cart_id",
            "order_id",
            "payment_id",
            "recommendation_id",
            "strategy_id",
            "keyword",
            "currency",
            "is_success",
        ],
        "metric_fields": [
            "result_count",
            "position",
            "quantity",
            "amount",
            "response_time_ms",
            "status_code",
        ],
        "trace_capable": True,
        "user_capable": True,
        "funnel_steps": list(_BEHAVIOR_FUNNEL_STEPS),
    },
    "application": {
        "filter_fields": _COMMON_FILTER_FIELDS
        + [
            "action",
            "request_path",
            "http_method",
            "status_code",
            "response_time_ms",
            "error_code",
            "exception_type",
            "upstream_service",
            "downstream_service",
            "interface_name",
            "db_operation",
            "db_table",
            "db_duration_ms",
            "redis_operation",
            "cache_key",
            "cache_hit",
            "retry_count",
            "order_id",
            "payment_id",
            "inventory_id",
        ],
        "terms_fields": _COMMON_TERMS_FIELDS
        + [
            "action",
            "request_path",
            "http_method",
            "error_code",
            "exception_type",
            "upstream_service",
            "downstream_service",
            "interface_name",
            "db_operation",
            "db_table",
            "redis_operation",
            "cache_key",
            "cache_hit",
            "status_code",
            "order_id",
            "payment_id",
            "inventory_id",
        ],
        "metric_fields": [
            "status_code",
            "response_time_ms",
            "db_duration_ms",
            "retry_count",
        ],
        "trace_capable": True,
        "user_capable": True,
    },
    "web_server": {
        "filter_fields": _COMMON_FILTER_FIELDS
        + [
            "nginx_log_kind",
            "remote_addr",
            "remote_user",
            "time_local",
            "request",
            "request_method",
            "request_uri",
            "uri",
            "query_string",
            "server_protocol",
            "status_code",
            "body_bytes_sent",
            "bytes_sent",
            "request_length",
            "http_referer",
            "http_user_agent",
            "http_x_forwarded_for",
            "host_header",
            "server_name",
            "scheme",
            "request_time",
            "upstream_addr",
            "upstream_status",
            "upstream_response_time",
            "upstream_connect_time",
            "upstream_header_time",
            "upstream_cache_status",
            "connection",
            "connection_requests",
            "pipe",
            "gzip_ratio",
            "ssl_protocol",
            "ssl_cipher",
            "error_level",
            "error_message",
            "response_time_ms",
        ],
        "terms_fields": _COMMON_TERMS_FIELDS
        + [
            "nginx_log_kind",
            "remote_addr",
            "remote_user",
            "request_method",
            "request_uri",
            "uri",
            "server_protocol",
            "status_code",
            "http_referer",
            "http_user_agent",
            "host_header",
            "server_name",
            "scheme",
            "upstream_addr",
            "upstream_status",
            "upstream_cache_status",
            "error_level",
            "pipe",
            "ssl_protocol",
            "ssl_cipher",
        ],
        "metric_fields": [
            "status_code",
            "body_bytes_sent",
            "bytes_sent",
            "request_length",
            "request_time",
            "upstream_response_time",
            "upstream_connect_time",
            "upstream_header_time",
            "connection_requests",
            "gzip_ratio",
            "response_time_ms",
        ],
        "trace_capable": True,
        "user_capable": True,
    },
    "performance": {
        "filter_fields": _COMMON_FILTER_FIELDS
        + [
            "metric_name",
            "metric_value",
            "metric_unit",
            "window_seconds",
            "qps",
            "tps",
            "p50_ms",
            "p95_ms",
            "p99_ms",
            "cpu_percent",
            "memory_percent",
            "disk_percent",
            "network_in_bytes",
            "network_out_bytes",
            "thread_pool_active",
            "connection_pool_in_use",
            "response_time_ms",
            "status_code",
        ],
        "terms_fields": _COMMON_TERMS_FIELDS
        + [
            "metric_name",
            "metric_unit",
        ],
        "metric_fields": [
            "metric_value",
            "window_seconds",
            "qps",
            "tps",
            "p50_ms",
            "p95_ms",
            "p99_ms",
            "cpu_percent",
            "memory_percent",
            "disk_percent",
            "network_in_bytes",
            "network_out_bytes",
            "thread_pool_active",
            "connection_pool_in_use",
            "response_time_ms",
            "status_code",
        ],
        "trace_capable": True,
        "user_capable": True,
    },
    "security": {
        "filter_fields": _COMMON_FILTER_FIELDS
        + [
            "action",
            "risk_level",
            "reason",
            "token_id",
            "is_token_valid",
            "ip_access_count",
            "device_id",
            "geo_location",
            "login_username",
            "is_blocked",
            "rule_id",
            "rule_name",
            "attack_type",
            "order_count_short_window",
            "crawler_score",
            "request_path",
            "response_time_ms",
            "status_code",
        ],
        "terms_fields": _COMMON_TERMS_FIELDS
        + [
            "action",
            "risk_level",
            "rule_id",
            "rule_name",
            "attack_type",
            "token_id",
            "device_id",
            "geo_location",
            "login_username",
            "is_token_valid",
            "is_blocked",
            "request_path",
            "status_code",
        ],
        "metric_fields": [
            "ip_access_count",
            "order_count_short_window",
            "crawler_score",
            "response_time_ms",
            "status_code",
        ],
        "trace_capable": True,
        "user_capable": True,
    },
    "infrastructure": {
        "filter_fields": _COMMON_FILTER_FIELDS
        + [
            "component",
            "resource_type",
            "severity",
            "cpu_percent",
            "memory_percent",
            "disk_percent",
            "disk_path",
            "pod_name",
            "container_id",
            "node_name",
            "cluster_name",
            "topic_name",
            "partition",
            "consumer_group",
            "lag",
            "es_index",
            "es_cluster_health",
            "request_path",
            "response_time_ms",
            "status_code",
        ],
        "terms_fields": _COMMON_TERMS_FIELDS
        + [
            "component",
            "resource_type",
            "severity",
            "disk_path",
            "pod_name",
            "container_id",
            "node_name",
            "cluster_name",
            "topic_name",
            "consumer_group",
            "es_index",
            "es_cluster_health",
            "request_path",
            "status_code",
        ],
        "metric_fields": [
            "cpu_percent",
            "memory_percent",
            "disk_percent",
            "lag",
            "partition",
            "response_time_ms",
            "status_code",
        ],
        "trace_capable": True,
        "user_capable": True,
    },
    "audit": {
        "filter_fields": _COMMON_FILTER_FIELDS
        + [
            "action",
            "operator_id",
            "operator_name",
            "operator_role",
            "target_type",
            "target_id",
            "target_name",
            "approval_id",
            "business_order_id",
            "is_manual",
            "change_summary",
            "response_time_ms",
            "status_code",
        ],
        "terms_fields": _COMMON_TERMS_FIELDS
        + [
            "action",
            "operator_id",
            "operator_name",
            "operator_role",
            "target_type",
            "target_id",
            "target_name",
            "approval_id",
            "business_order_id",
            "is_manual",
            "status_code",
        ],
        "metric_fields": [
            "response_time_ms",
            "status_code",
        ],
        "trace_capable": True,
        "user_capable": False,
    },
}

_REGISTERED_LOG_TYPES: list[str] = [
    "behavior",
    "application",
    "web_server",
    "performance",
    "security",
    "infrastructure",
    "audit",
]


def get_catalog_for_log_type(log_type: str) -> dict[str, Any]:
    """已知类型返回完整目录；未知类型返回 ok=False 与明确 message，不含 placeholder 键。"""
    if log_type in FIELD_CATALOG:
        return dict(FIELD_CATALOG[log_type])
    return {
        "ok": False,
        "message": f"未知的 log_type: {log_type}，当前仅支持: {', '.join(_REGISTERED_LOG_TYPES)}",
    }


def list_registered_log_types() -> list[str]:
    """固定返回 7 个 log_type。"""
    return list(_REGISTERED_LOG_TYPES)


def validate_aggregate_field(log_type: str, field: str, field_kind: str) -> bool:
    """field_kind 取值：filter | terms | metric。"""
    if field_kind not in {"filter", "terms", "metric"}:
        return False
    if log_type not in FIELD_CATALOG:
        return False
    catalog = FIELD_CATALOG[log_type]
    allowed_key = f"{field_kind}_fields"
    allowed = catalog.get(allowed_key, [])
    return field in allowed


def _log_type_to_index_segment(log_type: str) -> str:
    """将 log_type 转为 ES 索引名片段，与 index_service / Logstash 保持一致。

    约定：索引名片段与 log_type 枚举值相同（保留下划线），例如 web_server 对应
    app-logs-web_server-*。component template 名 logs-web-server 仅用于 ES 模板组合，
    不影响实际索引名。
    """
    return log_type


def resolve_index_pattern(log_types: list[str] | None = None) -> str:
    """将 log_type 列表转为 ES index pattern。

    - None 或空列表：使用 settings.elasticsearch_index_pattern（默认 app-logs-*）
    - 单类型：app-logs-{log_type}-*，如 app-logs-application-*、app-logs-web_server-*
    - 多类型：逗号拼接，如 app-logs-application-*,app-logs-web_server-*
    """
    from app.core.config import settings

    if not log_types:
        return settings.elasticsearch_index_pattern

    patterns = [f"app-logs-{_log_type_to_index_segment(lt)}-*" for lt in log_types]
    if len(patterns) == 1:
        return patterns[0]
    return ",".join(patterns)


def _collect_union_fields(field_key: str) -> set[str]:
    """收集全部 catalog 中某类字段的并集。"""
    result: set[str] = set()
    for catalog in FIELD_CATALOG.values():
        result.update(catalog.get(field_key, []))
    return result


def validate_aggregate_request(
    log_types: list[str] | None,
    group_by: str,
    metric_field: str | None = None,
) -> dict[str, Any]:
    """返回 {"ok": bool, "errors": list[str]}。

    校验 group_by 在 terms_fields 内；metric_field 在 metric_fields 内。
    log_types 为空时，group_by 须在任一类 catalog 的 terms_fields 并集内。
    """
    errors: list[str] = []

    if not log_types:
        all_terms = _collect_union_fields("terms_fields")
        if group_by not in all_terms:
            errors.append(
                f"group_by 字段 '{group_by}' 不在任一 log_type 的 terms_fields 白名单内"
            )
        if metric_field is not None:
            all_metrics = _collect_union_fields("metric_fields")
            if metric_field not in all_metrics:
                errors.append(
                    f"metric_field 字段 '{metric_field}' 不在任一 log_type 的 metric_fields 白名单内"
                )
    else:
        for lt in log_types:
            if lt not in FIELD_CATALOG:
                errors.append(f"未知的 log_type: {lt}")
                continue
            catalog = FIELD_CATALOG[lt]
            if group_by not in catalog.get("terms_fields", []):
                errors.append(
                    f"group_by 字段 '{group_by}' 不在 log_type={lt} 的 terms_fields 白名单内"
                )
            if metric_field is not None and metric_field not in catalog.get("metric_fields", []):
                errors.append(
                    f"metric_field 字段 '{metric_field}' 不在 log_type={lt} 的 metric_fields 白名单内"
                )

    return {"ok": len(errors) == 0, "errors": errors}
