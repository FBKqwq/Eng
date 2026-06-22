"""声明式规则表。

职责：阈值规则、错误码规则、频率规则的集中声明，供 rule_engine 读取。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §1.3 diagnosis 域改造
"""

from __future__ import annotations

from typing import Any, Literal

RuleKind = Literal["threshold", "error_code", "frequency"]

# 错误码规则：命中后触发规则子图（trigger_subgraph=True）
_ERROR_CODE_RULES: list[dict[str, Any]] = [
    {
        "rule_id": "R_PAY_FAIL",
        "rule_name": "支付失败",
        "kind": "error_code",
        "match": {"error_code": "PAY_FAIL"},
        "severity": "high",
        "trigger_subgraph": True,
    },
    {
        "rule_id": "R_DB_TIMEOUT",
        "rule_name": "数据库超时",
        "kind": "error_code",
        "match": {"error_code": "DB_TIMEOUT"},
        "severity": "high",
        "trigger_subgraph": True,
    },
    {
        "rule_id": "R_CIRCUIT_OPEN",
        "rule_name": "熔断开启",
        "kind": "error_code",
        "match": {"error_code": "CIRCUIT_OPEN"},
        "severity": "critical",
        "trigger_subgraph": True,
    },
    {
        "rule_id": "R_UNAVAILABLE",
        "rule_name": "服务不可用",
        "kind": "error_code",
        "match": {"error_code": "UNAVAILABLE"},
        "severity": "critical",
        "trigger_subgraph": True,
    },
]

# 阈值规则：单条日志字段数值比较
_THRESHOLD_RULES: list[dict[str, Any]] = [
    {
        "rule_id": "R_STATUS_CODE_5XX",
        "rule_name": "HTTP 5xx 服务错误",
        "kind": "threshold",
        "match": {"field": "status_code", "operator": ">=", "value": 500},
        "severity": "high",
        "trigger_subgraph": True,
    },
    {
        "rule_id": "R_RESPONSE_TIME_SLOW",
        "rule_name": "应用响应过慢",
        "kind": "threshold",
        "match": {"field": "response_time_ms", "operator": ">", "value": 3000},
        "severity": "medium",
        "trigger_subgraph": False,
    },
    {
        "rule_id": "R_REQUEST_TIME_SLOW",
        "rule_name": "网关请求耗时过长",
        "kind": "threshold",
        "match": {"field": "request_time", "operator": ">", "value": 3},
        "severity": "medium",
        "trigger_subgraph": False,
    },
]

# 频率规则：依赖 aggregation 计数，单条日志匹配由 rule_engine 在 M5-04 实现
_FREQUENCY_RULES: list[dict[str, Any]] = [
    {
        "rule_id": "R_FREQ_SERVICE_ERROR",
        "rule_name": "同服务短时 ERROR 激增",
        "kind": "frequency",
        "match": {
            "group_by": "service_name",
            "log_level": "ERROR",
            "window_minutes": 5,
            "min_count": 10,
        },
        "severity": "high",
        "trigger_subgraph": True,
    },
    {
        "rule_id": "R_FREQ_IP_ACCESS",
        "rule_name": "同 IP 高频访问",
        "kind": "frequency",
        "match": {
            "group_by": "client_ip",
            "window_minutes": 1,
            "min_count": 100,
        },
        "severity": "medium",
        "trigger_subgraph": False,
    },
    {
        "rule_id": "R_FREQ_USER_FAIL",
        "rule_name": "同用户连续失败",
        "kind": "frequency",
        "match": {
            "group_by": "user_id",
            "log_level": "ERROR",
            "window_minutes": 10,
            "min_count": 5,
        },
        "severity": "high",
        "trigger_subgraph": True,
    },
]

RULE_DEFINITIONS: list[dict[str, Any]] = [
    *_ERROR_CODE_RULES,
    *_THRESHOLD_RULES,
    *_FREQUENCY_RULES,
]


def get_rule_definitions() -> list[dict[str, Any]]:
    """返回当前生效的规则声明列表。"""
    return list(RULE_DEFINITIONS)
