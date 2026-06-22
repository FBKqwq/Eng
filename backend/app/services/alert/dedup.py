"""预警去重与幂等。

职责：幂等键 = alert_type + affected_service + 时间桶；重复则返回 existing_alert_id 供累加 evidence_count。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §1.3 / §3.2
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.elasticsearch.client import get_es_client

ALERT_INDEX_PATTERN = "alerts-*"
ES_REQUEST_TIMEOUT_SECONDS = 2
STATUS_ACTIVE = "active"


def build_idempotency_key(alert_candidate: dict[str, Any], *, bucket_minutes: int = 10) -> str:
  """构建幂等键：alert_type + affected_service + 时间桶起始时刻。"""
  alert_type = _normalize_field(alert_candidate.get("alert_type"), fallback="unknown")
  affected_service = _normalize_field(alert_candidate.get("affected_service"), fallback="unknown")
  bucket_start = _resolve_bucket_start(alert_candidate, bucket_minutes=bucket_minutes)
  bucket_label = bucket_start.strftime("%Y-%m-%dT%H:%M:%SZ")
  return f"{alert_type}:{affected_service}:{bucket_label}"


def check_duplicate(alert_candidate: dict[str, Any], *, bucket_minutes: int = 10) -> dict[str, Any]:
  """检查同桶内是否已有活跃预警；命中返回 existing_alert_id 供调用方累加 evidence_count。"""
  effective_bucket_minutes = max(1, int(bucket_minutes))
  idempotency_key = build_idempotency_key(
    alert_candidate,
    bucket_minutes=effective_bucket_minutes,
  )
  alert_type = _normalize_field(alert_candidate.get("alert_type"), fallback="unknown")
  affected_service = _normalize_field(alert_candidate.get("affected_service"), fallback="unknown")
  bucket_start = _resolve_bucket_start(alert_candidate, bucket_minutes=effective_bucket_minutes)
  bucket_end = bucket_start + timedelta(minutes=effective_bucket_minutes)

  query = {
    "bool": {
      "filter": [
        {"term": {"alert_type": alert_type}},
        {"term": {"status": STATUS_ACTIVE}},
        _affected_service_filter(affected_service),
        {
          "range": {
            "created_at": {
              "gte": _to_iso(bucket_start),
              "lt": _to_iso(bucket_end),
            }
          }
        },
      ]
    }
  }

  try:
    client = get_es_client().options(
      request_timeout=ES_REQUEST_TIMEOUT_SECONDS,
      max_retries=0,
    )
    response = client.search(
      index=ALERT_INDEX_PATTERN,
      query=query,
      size=1,
      sort=[{"created_at": {"order": "desc", "unmapped_type": "date"}}],
      ignore_unavailable=True,
      allow_no_indices=True,
    )
    data = _to_dict(response)
    hits = (data.get("hits") or {}).get("hits") or []
    if not hits:
      return {
        "ok": True,
        "is_duplicate": False,
        "existing_alert_id": None,
        "idempotency_key": idempotency_key,
      }

    hit = _to_dict(hits[0])
    source = hit.get("_source") or {}
    if not isinstance(source, dict):
      source = {}
    existing_alert_id = _coerce_str(source.get("alert_id") or hit.get("_id")).strip() or None
    return {
      "ok": True,
      "is_duplicate": True,
      "existing_alert_id": existing_alert_id,
      "idempotency_key": idempotency_key,
    }
  except Exception as exc:  # noqa: BLE001 — 结构化错误，不向上抛裸异常
    return {
      "ok": False,
      "error": str(exc),
      "is_duplicate": False,
      "existing_alert_id": None,
      "idempotency_key": idempotency_key,
    }


def _resolve_bucket_start(alert_candidate: dict[str, Any], *, bucket_minutes: int) -> datetime:
  created_at = alert_candidate.get("created_at")
  if created_at is None:
    dt = datetime.now(timezone.utc)
  else:
    dt = _parse_datetime(created_at)
  return _floor_to_bucket(dt, bucket_minutes=max(1, int(bucket_minutes)))


def _floor_to_bucket(dt: datetime, *, bucket_minutes: int) -> datetime:
  if dt.tzinfo is None:
    dt = dt.replace(tzinfo=timezone.utc)
  dt = dt.astimezone(timezone.utc).replace(microsecond=0)
  epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
  total_seconds = int((dt - epoch).total_seconds())
  bucket_seconds = bucket_minutes * 60
  floored_seconds = (total_seconds // bucket_seconds) * bucket_seconds
  return epoch + timedelta(seconds=floored_seconds)


def _affected_service_filter(affected_service: str) -> dict[str, Any]:
  if affected_service == "unknown":
    return {
      "bool": {
        "should": [
          {"bool": {"must_not": [{"exists": {"field": "affected_service"}}]}},
          {"term": {"affected_service": ""}},
        ],
        "minimum_should_match": 1,
      }
    }
  return {"term": {"affected_service": affected_service}}


def _parse_datetime(value: Any) -> datetime:
  if isinstance(value, datetime):
    if value.tzinfo is None:
      return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

  text = _coerce_str(value).strip()
  if not text:
    return datetime.now(timezone.utc)

  normalized = text.replace("Z", "+00:00")
  try:
    parsed = datetime.fromisoformat(normalized)
  except ValueError:
    return datetime.now(timezone.utc)
  if parsed.tzinfo is None:
    return parsed.replace(tzinfo=timezone.utc)
  return parsed.astimezone(timezone.utc)


def _to_iso(dt: datetime) -> str:
  return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_field(value: Any, *, fallback: str) -> str:
  text = _coerce_str(value).strip()
  return text or fallback


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
