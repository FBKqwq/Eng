"""Elasticsearch 相关 Agent 工具（占位）。

包装：log_query_service / aggregation_service / context_service。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §3.2 工具 1-5
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.log import LogType, TimeInterval

_PLACEHOLDER = {"ok": False, "placeholder": True}


class EsSearchLogsInput(BaseModel):
  keyword: Optional[str] = None
  log_type: Optional[LogType] = None
  start_time: Optional[datetime] = None
  end_time: Optional[datetime] = None
  limit: int = Field(default=50, le=50)


class EsAggregateMetricsInput(BaseModel):
  template: Literal["traffic", "errors", "latency", "behavior_funnel", "security", "infra_health"]
  log_types: Optional[list[LogType]] = None
  start_time: datetime
  end_time: datetime
  interval: Optional[TimeInterval] = None
  top_n: int = Field(default=10, le=50)


def es_search_logs(params: EsSearchLogsInput) -> dict[str, Any]:
  """工具 1：搜索日志样本（占位）。"""
  return {**_PLACEHOLDER, "tool": "es_search_logs", "params": params.model_dump(mode="json")}


def es_aggregate_metrics(params: EsAggregateMetricsInput) -> dict[str, Any]:
  """工具 2：六模板聚合统一入口（占位）。"""
  return {**_PLACEHOLDER, "tool": "es_aggregate_metrics", "params": params.model_dump(mode="json")}


def es_get_trace_context(trace_id: str, *, limit: int = 50) -> dict[str, Any]:
  """工具 3：trace 上下文（占位）。"""
  return {**_PLACEHOLDER, "tool": "es_get_trace_context", "trace_id": trace_id, "limit": limit}


def es_get_service_window(service: str, start_time: datetime, end_time: datetime) -> dict[str, Any]:
  """工具 4：服务窗口上下文（占位）。"""
  return {
    **_PLACEHOLDER,
    "tool": "es_get_service_window",
    "service": service,
    "start_time": start_time.isoformat(),
    "end_time": end_time.isoformat(),
  }


def es_get_similar_errors(error_code: str, start_time: datetime, end_time: datetime) -> dict[str, Any]:
  """工具 5：同类错误分布（占位）。"""
  return {
    **_PLACEHOLDER,
    "tool": "es_get_similar_errors",
    "error_code": error_code,
    "start_time": start_time.isoformat(),
    "end_time": end_time.isoformat(),
  }
