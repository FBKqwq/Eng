"""分析编排内部模型。

职责：TriggerEvent 标准化、节点追踪记录结构。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.3 / §2.6
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.core.config import settings

TriggerType = Literal["scheduled", "rule"]
NodeRunStatus = Literal["pending", "running", "success", "failed", "skipped"]

_VALID_TRIGGER_TYPES: frozenset[str] = frozenset({"scheduled", "rule"})


class TriggerEvent(BaseModel):
    """统一定时/规则两种触发输入。"""

    trigger_type: TriggerType
    trigger_event: dict[str, Any] = Field(default_factory=dict)
    time_window: dict[str, Any] = Field(default_factory=dict)
    source: str = ""


class NodeTraceEntry(BaseModel):
    """单节点执行记录，供前端展示图运行过程。"""

    node_name: str
    status: NodeRunStatus = "pending"
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_ms: int | None = None
    output_summary: str | None = None
    error_message: str | None = None


def _parse_trigger_type(raw: dict[str, Any]) -> str | None:
    value = raw.get("trigger_type")
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized not in _VALID_TRIGGER_TYPES:
        return None
    return normalized


def _default_time_window() -> dict[str, str]:
    # 必须使用 UTC aware 时间：日志 timestamp 以 UTC 存储，若用 naive 本地时间，
    # isoformat() 无时区后缀会被 ES 当作 UTC 解释，在非 UTC 时区造成窗口整体偏移、查不到数据。
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=settings.analysis_schedule_minutes)
    return {"start": start.isoformat(), "end": end.isoformat()}


def _complete_time_window(existing: Any) -> dict[str, Any]:
    if not isinstance(existing, dict) or not existing:
        return _default_time_window()
    window = dict(existing)
    default = _default_time_window()
    if not window.get("start"):
        window["start"] = default["start"]
    if not window.get("end"):
        window["end"] = default["end"]
    return window


def _extract_scheduled_trigger_event(raw: dict[str, Any]) -> dict[str, Any]:
    event = raw.get("trigger_event")
    if isinstance(event, dict):
        return dict(event)
    result: dict[str, Any] = {}
    if "task_name" in raw:
        result["task_name"] = raw["task_name"]
    return result


def _extract_rule_trigger_event(raw: dict[str, Any]) -> dict[str, Any]:
    event = raw.get("trigger_event")
    if isinstance(event, dict):
        return dict(event)
    legacy = raw.get("event")
    if isinstance(legacy, dict):
        result = dict(legacy)
        if "trigger_rule" in raw and "trigger_rule" not in result:
            result["trigger_rule"] = raw["trigger_rule"]
        return result
    if "trigger_rule" in raw:
        return {"trigger_rule": raw["trigger_rule"]}
    return {}


def _resolve_source(raw: dict[str, Any], trigger_type: str) -> str:
    source = raw.get("source")
    if isinstance(source, str) and source.strip():
        return source.strip()
    return "scheduler" if trigger_type == "scheduled" else "trigger_scanner"


def make_node_trace(
    node_name: str,
    status: NodeRunStatus = "pending",
    *,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    duration_ms: int | None = None,
    output_summary: str | None = None,
    error_message: str | None = None,
) -> dict[str, Any]:
    """基于 NodeTraceEntry 构造单条节点追踪记录。"""
    entry = NodeTraceEntry(
        node_name=node_name,
        status=status,
        started_at=started_at,
        ended_at=ended_at,
        duration_ms=duration_ms,
        output_summary=output_summary,
        error_message=error_message,
    )
    return entry.model_dump(mode="json")


def normalize_trigger(raw: dict[str, Any]) -> dict[str, Any]:
    """把原始触发输入标准化为 TriggerEvent。"""
    if not isinstance(raw, dict):
        return {"ok": False, "error": "invalid trigger_type"}

    trigger_type = _parse_trigger_type(raw)
    if trigger_type is None:
        return {"ok": False, "error": "invalid trigger_type"}

    try:
        if trigger_type == "scheduled":
            trigger = TriggerEvent(
                trigger_type="scheduled",
                trigger_event=_extract_scheduled_trigger_event(raw),
                time_window=_complete_time_window(raw.get("time_window")),
                source=_resolve_source(raw, "scheduled"),
            )
        else:
            trigger = TriggerEvent(
                trigger_type="rule",
                trigger_event=_extract_rule_trigger_event(raw),
                time_window=dict(raw["time_window"])
                if isinstance(raw.get("time_window"), dict)
                else {},
                source=_resolve_source(raw, "rule"),
            )
    except Exception:
        return {"ok": False, "error": "invalid trigger_type"}

    return {"ok": True, "trigger": trigger.model_dump(mode="json")}
