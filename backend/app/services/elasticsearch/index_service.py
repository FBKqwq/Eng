"""索引模板与生命周期管理。

职责：创建 component/index template，校验 mapping 与 schemas/log.py 一致。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §1.2.1
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from elasticsearch import ApiError, ConnectionError, TransportError

from app.services.elasticsearch.client import get_es_client

logger = logging.getLogger(__name__)

# 规划中的索引命名：app-logs-{log_type}-{yyyy.MM.dd}
INDEX_PREFIX = "app-logs"
LOG_TYPES = [
    "behavior",
    "application",
    "web_server",
    "performance",
    "security",
    "infrastructure",
    "audit",
]

_LOG_TYPE_TO_COMPONENT: dict[str, str] = {
    "behavior": "logs-behavior",
    "application": "logs-application",
    "web_server": "logs-web-server",
    "performance": "logs-performance",
    "security": "logs-security",
    "infrastructure": "logs-infrastructure",
    "audit": "logs-audit",
}

_COMPONENT_TEMPLATE_NAMES = ["logs-common", *_LOG_TYPE_TO_COMPONENT.values()]

_INDEX_TEMPLATE_NAMES = [f"{INDEX_PREFIX}-{log_type}" for log_type in LOG_TYPES]

_ANALYSIS_INDEX_TEMPLATE_NAMES = ["analysis-results", "alerts"]

_INDEX_TEMPLATE_PRIORITY = 200
_ANALYSIS_TEMPLATE_PRIORITY = 100


def _text_with_keyword(ignore_above: int = 256) -> dict[str, Any]:
    return {
        "type": "text",
        "fields": {"keyword": {"type": "keyword", "ignore_above": ignore_above}},
    }


def _common_properties() -> dict[str, Any]:
    """LogBase 公共字段 mapping，与 schemas/log.py 对齐。"""
    return {
        "timestamp": {"type": "date"},
        "log_id": {"type": "keyword"},
        "log_level": {"type": "keyword"},
        "log_type": {"type": "keyword"},
        "event_type": {"type": "keyword"},
        "service_name": {"type": "keyword"},
        "service_instance": {"type": "keyword"},
        "host": {"type": "keyword"},
        "env": {"type": "keyword"},
        "message": _text_with_keyword(),
        "source_type": {"type": "keyword"},
        "trace_id": {"type": "keyword"},
        "span_id": {"type": "keyword"},
        "request_id": {"type": "keyword"},
        "user_id": {"type": "keyword"},
        "session_id": {"type": "keyword"},
        "client_ip": {"type": "keyword"},
        "user_agent": {"type": "keyword"},
        "status": {"type": "keyword"},
        "tags": {"type": "keyword"},
        "extra": {"type": "object", "enabled": True},
    }


def _behavior_properties() -> dict[str, Any]:
    return {
        "action": {"type": "keyword"},
        "page": {"type": "keyword"},
        "module": {"type": "keyword"},
        "product_id": {"type": "keyword"},
        "product_name": {"type": "keyword"},
        "category_id": {"type": "keyword"},
        "cart_id": {"type": "keyword"},
        "order_id": {"type": "keyword"},
        "payment_id": {"type": "keyword"},
        "recommendation_id": {"type": "keyword"},
        "strategy_id": {"type": "keyword"},
        "keyword": {"type": "keyword"},
        "result_count": {"type": "long"},
        "position": {"type": "long"},
        "quantity": {"type": "long"},
        "amount": {"type": "float"},
        "currency": {"type": "keyword"},
        "is_success": {"type": "boolean"},
    }


def _application_properties() -> dict[str, Any]:
    return {
        "action": {"type": "keyword"},
        "request_path": {"type": "keyword"},
        "http_method": {"type": "keyword"},
        "status_code": {"type": "long"},
        "response_time_ms": {"type": "long"},
        "error_code": {"type": "keyword"},
        "exception_type": {"type": "keyword"},
        "upstream_service": {"type": "keyword"},
        "downstream_service": {"type": "keyword"},
        "interface_name": {"type": "keyword"},
        "db_operation": {"type": "keyword"},
        "db_table": {"type": "keyword"},
        "db_duration_ms": {"type": "long"},
        "redis_operation": {"type": "keyword"},
        "cache_key": {"type": "keyword"},
        "cache_hit": {"type": "boolean"},
        "retry_count": {"type": "long"},
        "order_id": {"type": "keyword"},
        "payment_id": {"type": "keyword"},
        "inventory_id": {"type": "keyword"},
    }


def _web_server_properties() -> dict[str, Any]:
    return {
        "nginx_log_kind": {"type": "keyword"},
        "remote_addr": {"type": "keyword"},
        "remote_user": {"type": "keyword"},
        "time_local": {"type": "keyword"},
        "request": _text_with_keyword(512),
        "request_method": {"type": "keyword"},
        "request_uri": {"type": "keyword"},
        "uri": {"type": "keyword"},
        "query_string": {"type": "keyword"},
        "server_protocol": {"type": "keyword"},
        "status_code": {"type": "long"},
        "body_bytes_sent": {"type": "long"},
        "bytes_sent": {"type": "long"},
        "request_length": {"type": "long"},
        "http_referer": {"type": "keyword"},
        "http_user_agent": _text_with_keyword(512),
        "http_x_forwarded_for": {"type": "keyword"},
        "host_header": {"type": "keyword"},
        "server_name": {"type": "keyword"},
        "scheme": {"type": "keyword"},
        "request_time": {"type": "float"},
        "upstream_addr": {"type": "keyword"},
        "upstream_status": {"type": "long"},
        "upstream_response_time": {"type": "float"},
        "upstream_connect_time": {"type": "float"},
        "upstream_header_time": {"type": "float"},
        "upstream_cache_status": {"type": "keyword"},
        "connection": {"type": "keyword"},
        "connection_requests": {"type": "long"},
        "pipe": {"type": "keyword"},
        "gzip_ratio": {"type": "float"},
        "ssl_protocol": {"type": "keyword"},
        "ssl_cipher": {"type": "keyword"},
        "error_level": {"type": "keyword"},
        "error_message": _text_with_keyword(512),
    }


def _performance_properties() -> dict[str, Any]:
    return {
        "metric_name": {"type": "keyword"},
        "metric_value": {"type": "float"},
        "metric_unit": {"type": "keyword"},
        "window_seconds": {"type": "long"},
        "qps": {"type": "float"},
        "tps": {"type": "float"},
        "p50_ms": {"type": "float"},
        "p95_ms": {"type": "float"},
        "p99_ms": {"type": "float"},
        "cpu_percent": {"type": "float"},
        "memory_percent": {"type": "float"},
        "disk_percent": {"type": "float"},
        "network_in_bytes": {"type": "long"},
        "network_out_bytes": {"type": "long"},
        "thread_pool_active": {"type": "long"},
        "connection_pool_in_use": {"type": "long"},
    }


def _security_properties() -> dict[str, Any]:
    return {
        "action": {"type": "keyword"},
        "risk_level": {"type": "keyword"},
        "reason": _text_with_keyword(),
        "token_id": {"type": "keyword"},
        "is_token_valid": {"type": "boolean"},
        "ip_access_count": {"type": "long"},
        "device_id": {"type": "keyword"},
        "geo_location": {"type": "keyword"},
        "login_username": {"type": "keyword"},
        "is_blocked": {"type": "boolean"},
        "rule_id": {"type": "keyword"},
        "rule_name": {"type": "keyword"},
        "attack_type": {"type": "keyword"},
        "order_count_short_window": {"type": "long"},
        "crawler_score": {"type": "float"},
    }


def _infrastructure_properties() -> dict[str, Any]:
    return {
        "component": {"type": "keyword"},
        "resource_type": {"type": "keyword"},
        "severity": {"type": "keyword"},
        "cpu_percent": {"type": "float"},
        "memory_percent": {"type": "float"},
        "disk_percent": {"type": "float"},
        "disk_path": {"type": "keyword"},
        "pod_name": {"type": "keyword"},
        "container_id": {"type": "keyword"},
        "node_name": {"type": "keyword"},
        "cluster_name": {"type": "keyword"},
        "topic_name": {"type": "keyword"},
        "partition": {"type": "long"},
        "consumer_group": {"type": "keyword"},
        "lag": {"type": "long"},
        "es_index": {"type": "keyword"},
        "es_cluster_health": {"type": "keyword"},
    }


def _audit_properties() -> dict[str, Any]:
    return {
        "action": {"type": "keyword"},
        "operator_id": {"type": "keyword"},
        "operator_name": {"type": "keyword"},
        "operator_role": {"type": "keyword"},
        "target_type": {"type": "keyword"},
        "target_id": {"type": "keyword"},
        "target_name": {"type": "keyword"},
        "before_value": {"type": "object", "enabled": True},
        "after_value": {"type": "object", "enabled": True},
        "change_summary": _text_with_keyword(),
        "approval_id": {"type": "keyword"},
        "business_order_id": {"type": "keyword"},
        "is_manual": {"type": "boolean"},
    }


def _type_specific_properties() -> dict[str, dict[str, Any]]:
    return {
        "behavior": _behavior_properties(),
        "application": _application_properties(),
        "web_server": _web_server_properties(),
        "performance": _performance_properties(),
        "security": _security_properties(),
        "infrastructure": _infrastructure_properties(),
        "audit": _audit_properties(),
    }


def _analysis_results_properties() -> dict[str, Any]:
    return {
        "report_id": {"type": "keyword"},
        "report_type": {"type": "keyword"},
        "title": _text_with_keyword(512),
        "risk_level": {"type": "keyword"},
        "summary": {"type": "text"},
        "status": {"type": "keyword"},
        "task_id": {"type": "keyword"},
        "created_at": {"type": "date"},
        "payload": {"type": "object", "enabled": True},
    }


def _alerts_properties() -> dict[str, Any]:
    return {
        "alert_id": {"type": "keyword"},
        "alert_type": {"type": "keyword"},
        "severity": {"type": "keyword"},
        "status": {"type": "keyword"},
        "title": _text_with_keyword(512),
        "affected_service": {"type": "keyword"},
        "evidence_count": {"type": "long"},
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
        "payload": {"type": "object", "enabled": True},
    }


def _default_index_settings() -> dict[str, Any]:
    return {
        "number_of_shards": 1,
        "number_of_replicas": 0,
    }


def _format_es_error(exc: Exception) -> str:
    if isinstance(exc, ApiError):
        status = getattr(exc, "status_code", None) or getattr(exc.meta, "status", None)
        if status == 401:
            return "Elasticsearch 认证失败（401），请检查用户名与密码"
        if status == 403:
            return "Elasticsearch 权限不足（403），需要 manage_index_templates 权限"
        body = getattr(exc, "body", None) or {}
        if isinstance(body, dict):
            err = body.get("error")
            if isinstance(err, dict) and err.get("reason"):
                return f"Elasticsearch API 错误（{status}）：{err['reason']}"
            if isinstance(err, str):
                return f"Elasticsearch API 错误（{status}）：{err}"
        return f"Elasticsearch API 错误（{status}）：{exc}"
    if isinstance(exc, (ConnectionError, TransportError)):
        return f"Elasticsearch 不可达：{exc}"
    return f"Elasticsearch 操作失败：{exc}"


def _run_es_action(action: str, fn: Callable[[], Any]) -> dict[str, Any]:
    try:
        result = fn()
        if isinstance(result, dict):
            return {"ok": True, "action": action, **result}
        return {"ok": True, "action": action, "result": result}
    except Exception as exc:  # noqa: BLE001 — 按任务要求不向调用方抛未捕获异常
        logger.warning("%s 失败: %s", action, exc)
        return {"ok": False, "action": action, "error": _format_es_error(exc)}


def _put_component_template(client: Any, name: str, properties: dict[str, Any]) -> None:
    client.cluster.put_component_template(
        name=name,
        template={
            "mappings": {
                "properties": properties,
            },
        },
    )


def _put_index_template(
    client: Any,
    *,
    name: str,
    index_patterns: list[str],
    composed_of: list[str] | None = None,
    properties: dict[str, Any] | None = None,
    priority: int = _INDEX_TEMPLATE_PRIORITY,
) -> None:
    template_body: dict[str, Any] = {
        "settings": _default_index_settings(),
    }
    if properties:
        template_body["mappings"] = {"properties": properties}
    kwargs: dict[str, Any] = {
        "name": name,
        "index_patterns": index_patterns,
        "priority": priority,
        "template": template_body,
    }
    if composed_of:
        kwargs["composed_of"] = composed_of
    client.indices.put_index_template(**kwargs)


def create_component_templates() -> dict[str, Any]:
    """创建 logs-common 及各类专有 component template。"""

    def _create() -> dict[str, Any]:
        client = get_es_client()
        type_props = _type_specific_properties()
        created: list[str] = []

        _put_component_template(client, "logs-common", _common_properties())
        created.append("logs-common")

        for log_type in LOG_TYPES:
            component_name = _LOG_TYPE_TO_COMPONENT[log_type]
            _put_component_template(client, component_name, type_props[log_type])
            created.append(component_name)

        return {"templates": created, "count": len(created)}

    return _run_es_action("create_component_templates", _create)


def create_index_templates() -> dict[str, Any]:
    """创建 7 个 index template：app-logs-{log_type}-*。"""

    def _create() -> dict[str, Any]:
        client = get_es_client()
        created: list[dict[str, str]] = []

        for log_type in LOG_TYPES:
            template_name = f"{INDEX_PREFIX}-{log_type}"
            pattern = f"{INDEX_PREFIX}-{log_type}-*"
            component_name = _LOG_TYPE_TO_COMPONENT[log_type]
            _put_index_template(
                client,
                name=template_name,
                index_patterns=[pattern],
                composed_of=["logs-common", component_name],
            )
            created.append(
                {
                    "name": template_name,
                    "index_pattern": pattern,
                    "composed_of": f"logs-common,{component_name}",
                }
            )

        return {"templates": created, "count": len(created), "log_types": LOG_TYPES}

    return _run_es_action("create_index_templates", _create)


def create_analysis_indices() -> dict[str, Any]:
    """创建 analysis-results-* 与 alerts-* 索引模板（M4/M5 预留）。"""

    def _create() -> dict[str, Any]:
        client = get_es_client()
        specs = [
            {
                "name": "analysis-results",
                "index_pattern": "analysis-results-*",
                "properties": _analysis_results_properties(),
            },
            {
                "name": "alerts",
                "index_pattern": "alerts-*",
                "properties": _alerts_properties(),
            },
        ]
        created: list[dict[str, str]] = []
        for spec in specs:
            _put_index_template(
                client,
                name=spec["name"],
                index_patterns=[spec["index_pattern"]],
                properties=spec["properties"],
                priority=_ANALYSIS_TEMPLATE_PRIORITY,
            )
            created.append(
                {
                    "name": spec["name"],
                    "index_pattern": spec["index_pattern"],
                }
            )
        return {"templates": created, "count": len(created)}

    return _run_es_action("create_analysis_indices", _create)


def init_all_indices() -> dict[str, Any]:
    """init_indices task 调用入口：依次创建全部模板与索引。"""
    steps = [
        create_component_templates(),
        create_index_templates(),
        create_analysis_indices(),
    ]
    failed = [step for step in steps if not step.get("ok")]
    if failed:
        return {
            "ok": False,
            "error": failed[0].get("error", "索引模板初始化失败"),
            "steps": steps,
        }
    return {"ok": True, "steps": steps}


def verify_templates() -> dict[str, Any]:
    """只读检查关键模板是否存在。"""
    missing: list[str] = []

    try:
        client = get_es_client()
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "missing": _COMPONENT_TEMPLATE_NAMES + _INDEX_TEMPLATE_NAMES + _ANALYSIS_INDEX_TEMPLATE_NAMES, "error": _format_es_error(exc)}

    for name in _COMPONENT_TEMPLATE_NAMES:
        try:
            client.cluster.get_component_template(name=name)
        except Exception:  # noqa: BLE001
            missing.append(f"component:{name}")

    for name in _INDEX_TEMPLATE_NAMES + _ANALYSIS_INDEX_TEMPLATE_NAMES:
        try:
            client.indices.get_index_template(name=name)
        except Exception:  # noqa: BLE001
            missing.append(f"index:{name}")

    return {"ok": len(missing) == 0, "missing": missing}
