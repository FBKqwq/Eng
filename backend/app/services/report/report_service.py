"""分析报告持久化。

职责：写入/查询 analysis-results-* 索引。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §1.3 report 域
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.services.elasticsearch.client import get_es_client

REPORT_INDEX_PATTERN = "analysis-results-*"
ES_REQUEST_TIMEOUT_SECONDS = 2
MAX_LIST_LIMIT = 100


def write_report(report: dict[str, Any]) -> dict[str, Any]:
  """写入分析报告到 analysis-results-* 索引。"""
  report_id = str(uuid4())
  created_at = _now_iso()
  document = {**report, "report_id": report_id, "created_at": created_at}
  index_name = _resolve_write_index(created_at)

  try:
    client = get_es_client().options(
      request_timeout=ES_REQUEST_TIMEOUT_SECONDS,
      max_retries=0,
    )
    client.index(index=index_name, id=report_id, document=document)
    return {"ok": True, "report_id": report_id}
  except Exception as exc:  # noqa: BLE001 — 结构化错误，不向上抛裸异常
    return {"ok": False, "error": str(exc)}


def list_recent_reports(limit: int = 20, report_type: str | None = None) -> dict[str, Any]:
  """按 created_at 倒序查询最近报告列表。"""
  effective_limit = max(1, min(int(limit), MAX_LIST_LIMIT))
  query = _build_list_query(report_type)
  sort = [{"created_at": {"order": "desc", "unmapped_type": "date"}}]

  try:
    client = get_es_client().options(
      request_timeout=ES_REQUEST_TIMEOUT_SECONDS,
      max_retries=0,
    )
    response = client.search(
      index=REPORT_INDEX_PATTERN,
      query=query,
      size=effective_limit,
      sort=sort,
      track_total_hits=True,
      ignore_unavailable=True,
      allow_no_indices=True,
    )
    data = _to_dict(response)
    hits_meta = data.get("hits") or {}
    total_meta = hits_meta.get("total", 0)
    total = int(total_meta.get("value", 0)) if isinstance(total_meta, dict) else int(total_meta or 0)
    hits = hits_meta.get("hits") or []
    items = [_hit_to_report_item(hit) for hit in hits]
    return {
      "ok": True,
      "items": items,
      "total": total,
      "limit": effective_limit,
    }
  except Exception as exc:  # noqa: BLE001
    return {
      "ok": False,
      "error": str(exc),
      "items": [],
      "total": 0,
      "limit": effective_limit,
    }


def get_report(report_id: str) -> dict[str, Any]:
  """按 report_id 查询单份报告。"""
  cleaned_id = (report_id or "").strip()
  if not cleaned_id:
    return {"ok": True, "report_id": report_id, "report": None}

  query = {"term": {"report_id": cleaned_id}}

  try:
    client = get_es_client().options(
      request_timeout=ES_REQUEST_TIMEOUT_SECONDS,
      max_retries=0,
    )
    response = client.search(
      index=REPORT_INDEX_PATTERN,
      query=query,
      size=1,
      ignore_unavailable=True,
      allow_no_indices=True,
    )
    data = _to_dict(response)
    hits = (data.get("hits") or {}).get("hits") or []
    if not hits:
      return {"ok": True, "report_id": cleaned_id, "report": None}
    report = _hit_to_report(hits[0])
    return {"ok": True, "report_id": cleaned_id, "report": report}
  except Exception as exc:  # noqa: BLE001
    return {
      "ok": False,
      "error": str(exc),
      "report_id": cleaned_id,
      "report": None,
    }


def _build_list_query(report_type: str | None) -> dict[str, Any]:
  cleaned_type = (report_type or "").strip()
  if cleaned_type:
    return {
      "bool": {
        "filter": [{"term": {"report_type": cleaned_type}}],
      }
    }
  return {"match_all": {}}


def _resolve_write_index(created_at: str) -> str:
  """按写入日期解析目标索引名，与 analysis-results-* 模板 pattern 对齐。"""
  date_part = created_at[:10]
  return f"analysis-results-{date_part}"


def _now_iso() -> str:
  return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _hit_to_report_item(hit: Any) -> dict[str, Any]:
  source = _extract_source(hit)
  hit_d = _to_dict(hit)
  return {
    "report_id": _coerce_str(source.get("report_id") or hit_d.get("_id")),
    "report_type": source.get("report_type"),
    "title": source.get("title") or "",
    "risk_level": source.get("risk_level"),
    "summary": source.get("summary") or "",
    "created_at": source.get("created_at"),
    "task_id": source.get("task_id"),
  }


def _hit_to_report(hit: Any) -> dict[str, Any]:
  return dict(_extract_source(hit))


def _extract_source(hit: Any) -> dict[str, Any]:
  source = _to_dict(hit).get("_source") or {}
  if not isinstance(source, dict):
    return {}
  return source


def _to_dict(value: Any) -> dict[str, Any]:
  if isinstance(value, dict):
    return value
  if hasattr(value, "to_dict"):
    return value.to_dict()
  try:
    return dict(value)
  except Exception:
    return {}


def _coerce_str(value: Any) -> str:
  return "" if value is None else str(value)
