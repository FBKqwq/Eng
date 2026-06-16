"""声明式规则表（占位）。

职责：阈值规则、错误码规则、频率规则的集中声明，供 rule_engine 读取。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §1.3 diagnosis 域改造
状态：占位 — RULE_DEFINITIONS 为空列表，当前仍由 classify_by_rules 关键词分流。
"""

from __future__ import annotations

from typing import Any, Literal

RuleKind = Literal["threshold", "error_code", "frequency"]

# 占位：规则结构示例
# {
#     "rule_id": "R_PAY_FAIL",
#     "rule_name": "支付失败",
#     "kind": "error_code",
#     "match": {"error_code": "PAY_FAIL"},
#     "severity": "high",
#     "trigger_subgraph": True,
# }

RULE_DEFINITIONS: list[dict[str, Any]] = []


def get_rule_definitions() -> list[dict[str, Any]]:
    """返回当前生效的规则声明列表（占位）。"""
    return list(RULE_DEFINITIONS)
