"""MCP / Agent 工具注册中心（占位）。

职责：LangChain StructuredTool 与 MCP Server 双形态出口。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §3.1 / §3.4
状态：占位 — 待 M2 注册第一阶段 10 个工具。
"""

from __future__ import annotations

from typing import Any


def get_langchain_tools(*, include_write_tools: bool = False) -> list[Any]:
  """返回进程内 LangChain 工具列表（占位）。"""
  return []


def create_mcp_server() -> Any:
  """基于 FastMCP 创建 MCP Server（占位，第二阶段）。"""
  return None


def list_registered_tool_names() -> list[str]:
  """返回已注册工具名称（占位）。"""
  return [
    "es_search_logs",
    "es_aggregate_metrics",
    "es_get_trace_context",
    "es_get_service_window",
    "es_get_similar_errors",
    "analysis_write_report",
    "alert_write_event",
    "alert_check_duplicate",
    "system_health_check",
    "rule_match_log",
  ]
