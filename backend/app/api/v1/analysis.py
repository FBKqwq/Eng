"""分析轨迹 API。

规划：GET /api/v1/analysis/runs/recent、POST /api/v1/analysis/run
职责：向前端暴露图执行 node_trace 与手动触发入口；薄路由，业务下沉 service。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field, field_validator

from app.schemas.response import ApiCode, ApiResponse, error_envelope, ok_envelope
from app.services.analysis.graph_main import run_main_graph
from app.services.report.report_service import get_report, list_recent_reports

router = APIRouter()

_VALID_TRIGGER_TYPES = frozenset({"scheduled", "rule"})
_TRACE_SUMMARY_KEYS = ("node_name", "status", "duration_ms", "output_summary")


class AnalysisRunRequest(BaseModel):
  """手动触发主图请求体。"""

  trigger_type: str
  trigger_event: dict[str, Any] = Field(default_factory=dict)
  time_window: dict[str, Any] = Field(default_factory=dict)

  @field_validator("trigger_type")
  @classmethod
  def validate_trigger_type(cls, value: str) -> str:
    normalized = (value or "").strip().lower()
    if normalized not in _VALID_TRIGGER_TYPES:
      raise ValueError("trigger_type must be scheduled or rule")
    return normalized


class NodeTraceSummary(BaseModel):
  node_name: str
  status: str
  duration_ms: int | None = None
  output_summary: str | None = None


class AnalysisRunItem(BaseModel):
  report_id: str
  report_type: str | None = None
  title: str = ""
  created_at: str | None = None
  trigger_type: str | None = None
  node_trace: list[NodeTraceSummary] = Field(default_factory=list)
  node_count: int = 0
  total_duration_ms: int = 0


# 统一信封 data 负载模型
class AnalysisRunsData(BaseModel):
  items: list[AnalysisRunItem] = Field(default_factory=list)
  total: int = 0
  limit: int = 20


class AnalysisRunData(BaseModel):
  report_id: str | None = None
  alert_id: str | None = None
  node_trace: list[dict[str, Any]] = Field(default_factory=list)
  alert_decision: dict[str, Any] = Field(default_factory=dict)
  errors: list[Any] = Field(default_factory=list)


def _summarize_node_trace(raw_trace: Any) -> list[dict[str, Any]]:
  if not isinstance(raw_trace, list):
    return []
  summaries: list[dict[str, Any]] = []
  for entry in raw_trace:
    if not isinstance(entry, dict):
      continue
    summary = {key: entry.get(key) for key in _TRACE_SUMMARY_KEYS if key in entry}
    if summary.get("node_name"):
      summaries.append(summary)
  return summaries


def _sum_duration_ms(trace: list[dict[str, Any]]) -> int:
  total = 0
  for entry in trace:
    duration = entry.get("duration_ms")
    if isinstance(duration, (int, float)) and duration >= 0:
      total += int(duration)
  return total


def _build_run_item(list_item: dict[str, Any], full_report: dict[str, Any] | None) -> AnalysisRunItem:
  report = full_report or {}
  trace = _summarize_node_trace(report.get("node_trace"))
  report_id = str(list_item.get("report_id") or report.get("report_id") or "")
  return AnalysisRunItem(
    report_id=report_id,
    report_type=list_item.get("report_type") or report.get("report_type"),
    title=str(list_item.get("title") or report.get("title") or ""),
    created_at=list_item.get("created_at") or report.get("created_at"),
    trigger_type=report.get("trigger_type"),
    node_trace=[NodeTraceSummary(**entry) for entry in trace],
    node_count=len(trace),
    total_duration_ms=_sum_duration_ms(trace),
  )


@router.get("/runs/recent", response_model=ApiResponse[AnalysisRunsData])
def recent_analysis_runs(limit: int = Query(default=20, ge=1, le=100)) -> ApiResponse[AnalysisRunsData]:
  """返回近期图执行 node_trace 摘要，供前端展示节点耗时与产出。"""
  result = list_recent_reports(limit=limit)
  if not result.get("ok"):
    return error_envelope(
      ApiCode.QUERY_FAILED,
      result.get("error") or result.get("message") or "list_recent_reports failed",
    )

  items: list[AnalysisRunItem] = []
  for list_item in result.get("items") or []:
    if not isinstance(list_item, dict):
      continue
    report_id = str(list_item.get("report_id") or "")
    full_report: dict[str, Any] | None = None
    if report_id:
      detail = get_report(report_id)
      if detail.get("ok") and isinstance(detail.get("report"), dict):
        full_report = detail["report"]
    items.append(_build_run_item(list_item, full_report))

  return ok_envelope(
    AnalysisRunsData(
      items=items,
      total=int(result.get("total") or 0),
      limit=int(result.get("limit") or limit),
    )
  )


@router.post("/run", response_model=ApiResponse[AnalysisRunData])
def run_analysis(payload: AnalysisRunRequest) -> ApiResponse[AnalysisRunData]:
  """手动触发主图执行，返回 node_trace 与 report_id/alert_id。"""
  kwargs: dict[str, Any] = {}
  if payload.trigger_event:
    kwargs["trigger_event"] = payload.trigger_event
  if payload.time_window:
    kwargs["time_window"] = payload.time_window

  result = run_main_graph(payload.trigger_type, **kwargs)
  data = AnalysisRunData(
    report_id=result.get("report_id"),
    alert_id=result.get("alert_id"),
    node_trace=list(result.get("node_trace") or []),
    alert_decision=dict(result.get("alert_decision") or {}),
    errors=list(result.get("errors") or []),
  )
  if not result.get("ok"):
    return error_envelope(ApiCode.GRAPH_FAILED, "main graph execution failed", data=data)
  return ok_envelope(data)
