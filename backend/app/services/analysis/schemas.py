"""分析编排内部模型（占位）。

职责：TriggerEvent 标准化、节点追踪记录结构。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.3 / §2.6
状态：占位 — 待 M4 实现。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

TriggerType = Literal["scheduled", "rule"]
NodeRunStatus = Literal["pending", "running", "success", "failed", "skipped"]


class TriggerEvent(BaseModel):
    """统一定时/规则两种触发输入。"""
    trigger_type: TriggerType
    trigger_event: dict[str, Any] = Field(default_factory=dict)
    time_window: dict[str, Any] = Field(default_factory=dict)
    source: str = "placeholder"


class NodeTraceEntry(BaseModel):
    """单节点执行记录，供前端展示图运行过程。"""
    node_name: str
    status: NodeRunStatus = "pending"
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_ms: int | None = None
    output_summary: str | None = None
    error_message: str | None = None


def normalize_trigger(raw: dict[str, Any]) -> dict[str, Any]:
    """把原始触发输入标准化为 TriggerEvent（占位）。"""
    return {
        "ok": False,
        "placeholder": True,
        "message": "normalize_trigger 尚未实现",
        "raw": raw,
    }
