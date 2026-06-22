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

from app.services.tools import alert_tools, elasticsearch_tools, kibana_tools, report_tools, rule_tools, system_tools

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
  "es_get_business_funnel",
  "es_detect_traffic_peak",
  "es_compare_time_windows",
  "kibana_generate_link",
  "report_list_recent",
  "alert_list_active",
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
    (
      "es_get_business_funnel",
      "【读】行为漏斗洞察，统计各环节转化与流失。",
      elasticsearch_tools.es_get_business_funnel,
      elasticsearch_tools.EsGetBusinessFunnelInput,
      True,
    ),
    (
      "es_detect_traffic_peak",
      "【读】请求高峰定位，识别时间桶峰值与 peak_bucket。",
      elasticsearch_tools.es_detect_traffic_peak,
      elasticsearch_tools.EsDetectTrafficPeakInput,
      True,
    ),
    (
      "es_compare_time_windows",
      "【读】双时间窗口指标对比，输出环比变化。",
      elasticsearch_tools.es_compare_time_windows,
      elasticsearch_tools.EsCompareTimeWindowsInput,
      True,
    ),
    (
      "kibana_generate_link",
      "【读】离线拼装 Kibana Discover 跳转链接，不访问网络。",
      kibana_tools.kibana_generate_link,
      kibana_tools.KibanaGenerateLinkInput,
      True,
    ),
    (
      "report_list_recent",
      "【读】查询最近分析报告列表。",
      report_tools.report_list_recent,
      report_tools.ReportListRecentInput,
      True,
    ),
    (
      "alert_list_active",
      "【读】查询当前活跃预警事件列表。",
      alert_tools.alert_list_active,
      alert_tools.AlertListActiveInput,
      True,
    ),
  ]


def get_langchain_tools(*, include_write_tools: bool = False) -> list[StructuredTool]:
  """返回进程内 LangChain StructuredTool 列表。

  默认仅暴露读类工具（1~5、8~10、11~16）；``include_write_tools=True`` 时追加写类工具 6、7。
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


def _structured_tool_to_mcp_callable(lc_tool: StructuredTool) -> Callable[..., dict[str, Any]]:
  """将 LangChain StructuredTool 适配为 FastMCP 可注册的可调用对象（避免 **kwargs 签名）。"""

  schema = lc_tool.args_schema
  if schema is None:

    def _runner() -> dict[str, Any]:
      return lc_tool.invoke({})

    _runner.__name__ = lc_tool.name
    _runner.__doc__ = lc_tool.description or ""
    return _runner

  input_schema = schema

  def _runner(params: input_schema) -> dict[str, Any]:  # type: ignore[name-defined]
    return lc_tool.invoke(params.model_dump())

  _runner.__name__ = lc_tool.name
  _runner.__doc__ = lc_tool.description or ""
  _runner.__annotations__ = {"params": input_schema, "return": dict[str, Any]}
  return _runner


def create_mcp_server() -> Any:
  """基于 FastMCP 创建 MCP Server，仅暴露读类工具。

  fastmcp 未安装时返回 ``{"ok": False, "error": "fastmcp 未安装"}``，不抛异常。
  成功时返回 FastMCP 实例，由 task 层调用 ``server.run()`` 常驻。
  """
  try:
    from fastmcp import FastMCP
  except ImportError:
    return {"ok": False, "error": "fastmcp 未安装"}

  mcp = FastMCP("elk-log-analysis")
  for lc_tool in get_langchain_tools(include_write_tools=False):
    mcp.add_tool(_structured_tool_to_mcp_callable(lc_tool))
  return mcp


def list_registered_tool_names() -> list[str]:
  """返回已注册工具名称（稳定顺序，共 16 个）。"""
  return list(_TOOL_NAMES)
