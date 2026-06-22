"""MCP / Agent 工具注册中心。

职责：LangChain StructuredTool 与 MCP Server 双形态出口。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §3.1 / §3.4
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.services.tools import alert_tools, elasticsearch_tools, report_tools, rule_tools, system_tools

# 稳定注册顺序（与 list_registered_tool_names 一致）
_TOOL_NAMES: list[str] = [
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

_WRITE_TOOL_NAMES: frozenset[str] = frozenset({"analysis_write_report", "alert_write_event"})


class EsGetTraceContextInput(BaseModel):
  trace_id: str = Field(description="分布式 trace 标识")
  limit: int = Field(default=50, le=50, description="返回日志条数上限")


class EsGetServiceWindowInput(BaseModel):
  service: str = Field(description="服务名称")
  start_time: datetime = Field(description="窗口起始时间")
  end_time: datetime = Field(description="窗口结束时间")


class EsGetSimilarErrorsInput(BaseModel):
  error_code: str = Field(description="错误码")
  start_time: datetime = Field(description="统计起始时间")
  end_time: datetime = Field(description="统计结束时间")


def _bind_model(func: Callable[..., dict[str, Any]], schema: type[BaseModel]) -> Callable[..., dict[str, Any]]:
  """将「单 Pydantic 入参」工具函数适配为 StructuredTool 可调用签名。"""

  def _runner(**kwargs: Any) -> dict[str, Any]:
    return func(schema(**kwargs))

  return _runner


def _build_tool(
  *,
  name: str,
  description: str,
  func: Callable[..., dict[str, Any]],
  args_schema: type[BaseModel] | None = None,
  model_bound: bool = False,
) -> StructuredTool:
  runner = _bind_model(func, args_schema) if model_bound and args_schema is not None else func
  if args_schema is not None:
    return StructuredTool.from_function(
      func=runner,
      name=name,
      description=description,
      args_schema=args_schema,
    )
  return StructuredTool.from_function(
    func=runner,
    name=name,
    description=description,
  )


def _all_tool_specs() -> list[tuple[str, str, Callable[..., dict[str, Any]], type[BaseModel] | None, bool]]:
  return [
    (
      "es_search_logs",
      "【读】搜索日志样本，支持关键词、日志类型与时间窗口过滤。",
      elasticsearch_tools.es_search_logs,
      elasticsearch_tools.EsSearchLogsInput,
      True,
    ),
    (
      "es_aggregate_metrics",
      "【读】按六类模板（流量/错误/延迟/行为漏斗/安全/基础设施）聚合指标。",
      elasticsearch_tools.es_aggregate_metrics,
      elasticsearch_tools.EsAggregateMetricsInput,
      True,
    ),
    (
      "es_get_trace_context",
      "【读】按 trace_id 拉取关联日志上下文。",
      elasticsearch_tools.es_get_trace_context,
      EsGetTraceContextInput,
      False,
    ),
    (
      "es_get_service_window",
      "【读】按服务名与时间窗口拉取服务级日志上下文。",
      elasticsearch_tools.es_get_service_window,
      EsGetServiceWindowInput,
      False,
    ),
    (
      "es_get_similar_errors",
      "【读】按错误码与时间窗口统计同类错误分布。",
      elasticsearch_tools.es_get_similar_errors,
      EsGetSimilarErrorsInput,
      False,
    ),
    (
      "analysis_write_report",
      "【写】持久化分析报告，仅 persist 节点或 include_write_tools=True 时暴露。",
      report_tools.analysis_write_report,
      report_tools.WriteReportInput,
      True,
    ),
    (
      "alert_write_event",
      "【写】写入预警事件，仅 persist 节点或 include_write_tools=True 时暴露。",
      alert_tools.alert_write_event,
      alert_tools.WriteAlertInput,
      True,
    ),
    (
      "alert_check_duplicate",
      "【读】检查候选预警是否在时间桶内重复。",
      alert_tools.alert_check_duplicate,
      alert_tools.CheckDuplicateInput,
      True,
    ),
    (
      "system_health_check",
      "【读】组合 Elasticsearch、Kafka 与 Docker 健康快照。",
      system_tools.system_health_check,
      None,
      False,
    ),
    (
      "rule_match_log",
      "【读】对单条日志事件复核规则命中结果。",
      rule_tools.rule_match_log,
      rule_tools.RuleMatchLogInput,
      True,
    ),
  ]


def get_langchain_tools(*, include_write_tools: bool = False) -> list[StructuredTool]:
  """返回进程内 LangChain StructuredTool 列表。

  默认仅暴露读类工具（1~5、8~10）；``include_write_tools=True`` 时追加写类工具 6、7。
  """
  tools: list[StructuredTool] = []
  for name, description, func, args_schema, model_bound in _all_tool_specs():
    if name in _WRITE_TOOL_NAMES and not include_write_tools:
      continue
    tools.append(
      _build_tool(
        name=name,
        description=description,
        func=func,
        args_schema=args_schema,
        model_bound=model_bound,
      )
    )
  return tools


def create_mcp_server() -> Any:
  """基于 FastMCP 创建 MCP Server（M7 实装，当前占位）。"""
  raise NotImplementedError("create_mcp_server 属 M7 里程碑，待 FastMCP 接入后实装")


def list_registered_tool_names() -> list[str]:
  """返回已注册工具名称（稳定顺序，共 10 个）。"""
  return list(_TOOL_NAMES)
