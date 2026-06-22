"""LangGraph 统一状态契约。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.2
职责：AnalysisState 结构定义、初始状态创建与 node_trace / errors 辅助。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, TypedDict
from uuid import uuid4

from app.services.analysis.schemas import NodeRunStatus, NodeTraceEntry

# 初始状态空容器默认值（create_initial_state 使用）
_EMPTY_CONTAINERS: dict[str, Any] = {
    "trigger_event": {},
    "time_window": {},
    "query_plan": {},
    "metrics": {},
    "raw_logs": [],
    "evidence_package": {},
    "relations": [],
    "analysis_report": {},
    "alert_candidate": {},
    "alert_decision": {},
    "persist_result": {},
    "node_trace": [],
    "errors": [],
}


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
    """创建初始图状态。

    生成 task_id（缺省 uuid4），初始化空容器，并合并 time_window、trigger_event 等传入字段。
    """
    task_id = kwargs.pop("task_id", None) or str(uuid4())

    state: dict[str, Any] = {
        "trigger_type": trigger_type,
        "task_id": task_id,
        **_EMPTY_CONTAINERS,
    }
    state.update(kwargs)
    return state  # type: ignore[return-value]


def append_node_trace(
    state: AnalysisState,
    node_name: str,
    status: NodeRunStatus,
    *,
    duration_ms: int | None = None,
    output_summary: str | None = None,
    error_message: str | None = None,
) -> None:
    """向 state["node_trace"] 追加一条节点执行记录（结构对齐 NodeTraceEntry）。"""
    ended_at: datetime | None = None
    started_at: datetime | None = None

    if duration_ms is not None:
        ended_at = datetime.now(UTC)
        started_at = ended_at - timedelta(milliseconds=duration_ms)
    elif status == "running":
        started_at = datetime.now(UTC)

    entry = NodeTraceEntry(
        node_name=node_name,
        status=status,
        started_at=started_at,
        ended_at=ended_at,
        duration_ms=duration_ms,
        output_summary=output_summary,
        error_message=error_message,
    )
    trace = state.setdefault("node_trace", [])
    trace.append(entry.model_dump(mode="json"))


def record_error(state: AnalysisState, node_name: str, message: str) -> None:
    """向 state["errors"] 追加节点级错误，供降级路径使用。"""
    errors = state.setdefault("errors", [])
    errors.append(
        {
            "node_name": node_name,
            "message": message,
            "recorded_at": datetime.now(UTC).isoformat(),
        }
    )
