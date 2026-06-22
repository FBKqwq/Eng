"""预警持久化。

职责：写入/查询 alerts-* 索引；状态机 active -> acknowledged -> resolved。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §1.3 alert 域
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.services.elasticsearch.client import get_es_client

ALERT_INDEX_PATTERN = "alerts-*"
ES_REQUEST_TIMEOUT_SECONDS = 2
MAX_LIST_LIMIT = 200
STATUS_ACTIVE = "active"
STATUS_ACKNOWLEDGED = "acknowledged"


def write_alert(alert: dict[str, Any]) -> dict[str, Any]:
  """写入预警事件到 alerts-* 索引；支持按 existing_alert_id 累加 evidence_count。"""
  existing_alert_id = _coerce_str(alert.get("existing_alert_id")).strip()
  if existing_alert_id:
    return _increment_evidence(existing_alert_id)

  now = _now_iso()
  alert_id = str(uuid4())
  document = _build_alert_document(alert, alert_id=alert_id, now=now)
  index_name = _resolve_write_index(now)

  try:
    client = get_es_client().options(
      request_timeout=ES_REQUEST_TIMEOUT_SECONDS,
      max_retries=0,
    )
    client.index(index=index_name, id=alert_id, document=document)
    return {"ok": True, "alert_id": alert_id}
  except Exception as exc:  # noqa: BLE001 — 结构化错误，不向上抛裸异常
    return {"ok": False, "error": str(exc)}


def list_active_alerts(limit: int = 50) -> dict[str, Any]:
  """查询 status=active 的预警，按 updated_at 倒序。"""
  effective_limit = max(1, min(int(limit), MAX_LIST_LIMIT))
  query = {
    "bool": {
      "filter": [{"term": {"status": STATUS_ACTIVE}}],
    }
  }
  sort = [{"updated_at": {"order": "desc", "unmapped_type": "date"}}]

  try:
    client = get_es_client().options(
      request_timeout=ES_REQUEST_TIMEOUT_SECONDS,
      max_retries=0,
    )
    response = client.search(
      index=ALERT_INDEX_PATTERN,
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
    items = [_hit_to_alert_item(hit) for hit in hits]
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


def acknowledge_alert(alert_id: str, operator: str | None = None) -> dict[str, Any]:
  """将预警状态从 active 流转为 acknowledged。"""
  cleaned_id = _coerce_str(alert_id).strip()
  if not cleaned_id:
    return {
      "ok": False,
      "error": "alert_id 不能为空",
      "alert_id": alert_id,
    }

  located = _find_active_alert(cleaned_id)
  if located is None:
    return {
      "ok": False,
      "error": f"未找到可确认的活跃预警: {cleaned_id}",
      "alert_id": cleaned_id,
    }

  now = _now_iso()
  source = located["source"]
  payload = dict(source.get("payload") or {})
  if operator:
    payload["acknowledged_by"] = operator
  payload["acknowledged_at"] = now
  update_doc = {
    "status": STATUS_ACKNOWLEDGED,
    "updated_at": now,
    "payload": payload,
  }

  try:
    client = get_es_client().options(
      request_timeout=ES_REQUEST_TIMEOUT_SECONDS,
      max_retries=0,
    )
    client.update(
      index=located["index"],
      id=located["_id"],
      doc=update_doc,
    )
    return {
      "ok": True,
      "alert_id": cleaned_id,
      "status": STATUS_ACKNOWLEDGED,
    }
  except Exception as exc:  # noqa: BLE001
    return {
      "ok": False,
      "error": str(exc),
      "alert_id": cleaned_id,
    }


def _increment_evidence(alert_id: str) -> dict[str, Any]:
  located = _find_alert_by_id(alert_id)
  if located is None:
    return {
      "ok": False,
      "error": f"未找到预警: {alert_id}",
      "alert_id": alert_id,
    }

  source = located["source"]
  current_count = int(source.get("evidence_count") or 0)
  now = _now_iso()
  update_doc = {
    "evidence_count": current_count + 1,
    "updated_at": now,
  }

  try:
    client = get_es_client().options(
      request_timeout=ES_REQUEST_TIMEOUT_SECONDS,
      max_retries=0,
    )
    client.update(
      index=located["index"],
      id=located["_id"],
      doc=update_doc,
    )
    return {"ok": True, "alert_id": alert_id}
  except Exception as exc:  # noqa: BLE001
    return {
      "ok": False,
      "error": str(exc),
      "alert_id": alert_id,
    }


def _find_active_alert(alert_id: str) -> dict[str, Any] | None:
  located = _find_alert_by_id(alert_id)
  if located is None:
    return None
  if _coerce_str(located["source"].get("status")) != STATUS_ACTIVE:
    return None
  return located


def _find_alert_by_id(alert_id: str) -> dict[str, Any] | None:
  query = {"term": {"alert_id": alert_id}}

  try:
    client = get_es_client().options(
      request_timeout=ES_REQUEST_TIMEOUT_SECONDS,
      max_retries=0,
    )
    response = client.search(
      index=ALERT_INDEX_PATTERN,
      query=query,
      size=1,
      ignore_unavailable=True,
      allow_no_indices=True,
    )
    data = _to_dict(response)
    hits = (data.get("hits") or {}).get("hits") or []
    if not hits:
      return None
    hit = _to_dict(hits[0])
    source = hit.get("_source") or {}
    if not isinstance(source, dict):
      source = {}
    return {
      "index": hit.get("_index"),
      "_id": hit.get("_id"),
      "source": source,
    }
  except Exception:
    return None


def _build_alert_document(alert: dict[str, Any], *, alert_id: str, now: str) -> dict[str, Any]:
  reserved = {
    "existing_alert_id",
    "alert_id",
    "status",
    "evidence_count",
    "created_at",
    "updated_at",
  }
  payload = alert.get("payload")
  if not isinstance(payload, dict):
    payload = {k: v for k, v in alert.items() if k not in reserved and v is not None}

  return {
    "alert_id": alert_id,
    "alert_type": alert.get("alert_type") or "unknown",
    "severity": alert.get("severity") or "medium",
    "status": STATUS_ACTIVE,
    "title": alert.get("title") or "",
    "affected_service": alert.get("affected_service"),
    "evidence_count": 1,
    "created_at": now,
    "updated_at": now,
    "payload": payload,
  }


def _resolve_write_index(updated_at: str) -> str:
  """按写入日期解析目标索引名，与 alerts-* 模板 pattern 对齐。"""
  date_part = updated_at[:10]
  return f"alerts-{date_part}"


def _hit_to_alert_item(hit: Any) -> dict[str, Any]:
  source = _extract_source(hit)
  hit_d = _to_dict(hit)
  return {
    "alert_id": _coerce_str(source.get("alert_id") or hit_d.get("_id")),
    "alert_type": source.get("alert_type") or "unknown",
    "severity": source.get("severity") or "medium",
    "status": source.get("status") or STATUS_ACTIVE,
    "title": source.get("title") or "",
    "affected_service": source.get("affected_service"),
    "evidence_count": int(source.get("evidence_count") or 1),
    "created_at": source.get("created_at"),
    "updated_at": source.get("updated_at"),
  }


def _extract_source(hit: Any) -> dict[str, Any]:
  source = _to_dict(hit).get("_source") or {}
  if not isinstance(source, dict):
    return {}
  return source


def _now_iso() -> str:
  return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
