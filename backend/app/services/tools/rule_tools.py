"""规则匹配 Agent 工具（占位）。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §3.2 工具 10
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class RuleMatchLogInput(BaseModel):
  log_event: dict[str, Any]


def rule_match_log(params: RuleMatchLogInput) -> dict[str, Any]:
  """工具 10：对单条日志复核规则命中（占位）。"""
  return {
    "ok": False,
    "placeholder": True,
    "tool": "rule_match_log",
    "message": "待 P1 接入 diagnosis.rule_engine.match_log",
    "log_event_id": params.log_event.get("log_id"),
  }
