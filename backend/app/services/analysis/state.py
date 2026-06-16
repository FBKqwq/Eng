"""LangGraph 统一状态契约（占位）。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.2
状态：占位 — TypedDict 结构已定义，待 M4/M5 接入 LangGraph。
"""

from __future__ import annotations

from typing import Any, TypedDict


class AnalysisState(TypedDict, total=False):
    # 触发上下文
    trigger_type: str            # "scheduled" | "rule"
    trigger_event: dict          # 规则触发时的原始日志事件
    time_window: dict            # {"start": ..., "end": ...}
    task_id: str                 # 本次图运行唯一 ID

    # 查询与证据
    query_plan: dict
    metrics: dict
    raw_logs: list
    evidence_package: dict

    # 分析结果
    relations: list
    analysis_report: dict
    alert_candidate: dict
    alert_decision: dict

    # 运行管理
    persist_result: dict
    node_trace: list
    errors: list


def create_initial_state(trigger_type: str, **kwargs: Any) -> AnalysisState:
    """创建初始图状态（占位）。"""
    return {
        "trigger_type": trigger_type,
        "task_id": kwargs.get("task_id", ""),
        "node_trace": [],
        "errors": [],
        **{k: v for k, v in kwargs.items() if k != "task_id"},
    }
