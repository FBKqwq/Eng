"""规则匹配 Agent 工具。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §3.2 工具 10
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.services.diagnosis.rule_engine import match_log


class RuleMatchLogInput(BaseModel):
  log_event: dict[str, Any]


def rule_match_log(params: RuleMatchLogInput) -> dict[str, Any]:
  """工具 10：对单条日志复核规则命中。"""
  try:
    result = match_log(params.log_event)
    response: dict[str, Any] = {**result, "tool": "rule_match_log"}
    response.pop("placeholder", None)
    return response
  except Exception as exc:
    return {
      "ok": False,
      "error": str(exc),
      "tool": "rule_match_log",
    }
