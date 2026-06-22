"""Kibana 链接生成 Agent 工具。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §3.2 工具 14
离线纯拼 Discover URL，不访问网络、不依赖 ES。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.core.config import settings
from app.schemas.log import LogType

DEFAULT_KIBANA_BASE_URL = "http://localhost:5601"
MAX_TIME_WINDOW_HOURS = 24


class KibanaGenerateLinkInput(BaseModel):
  index_pattern: str = Field(..., min_length=1, description="Kibana 数据视图索引模式，如 app-logs-*")
  start_time: datetime
  end_time: datetime
  query: Optional[str] = Field(default=None, description="KQL 或关键词查询")
  log_type: Optional[LogType] = Field(default=None, description="可选日志类型过滤")


def _resolve_kibana_base_url() -> str:
  base = getattr(settings, "kibana_base_url", None)
  if base and str(base).strip():
    return str(base).strip().rstrip("/")
  return DEFAULT_KIBANA_BASE_URL


def _to_utc_iso(dt: datetime) -> str:
  if dt.tzinfo is None:
    dt = dt.replace(tzinfo=timezone.utc)
  else:
    dt = dt.astimezone(timezone.utc)
  return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _rison_escape(value: str) -> str:
  return value.replace("\\", "\\\\").replace("'", "\\'")


def _build_kql_query(query: Optional[str], log_type: Optional[LogType]) -> str:
  parts: list[str] = []
  if query and query.strip():
    parts.append(f"({query.strip()})")
  if log_type is not None:
    parts.append(f'log_type: "{log_type.value}"')
  return " and ".join(parts)


def _build_discover_url(
  *,
  base_url: str,
  index_pattern: str,
  start_time: datetime,
  end_time: datetime,
  kql_query: str,
) -> str:
  from_iso = _to_utc_iso(start_time)
  to_iso = _to_utc_iso(end_time)
  escaped_index = _rison_escape(index_pattern.strip())
  escaped_query = _rison_escape(kql_query)

  global_state = (
    f"(filters:!(),refreshInterval:(pause:!t,value:0),"
    f"time:(from:'{from_iso}',to:'{to_iso}'))"
  )
  app_state = (
    f"(columns:!(),filters:!(),index:'{escaped_index}',interval:auto,"
    f"query:(language:kuery,query:'{escaped_query}'),"
    f"sort:!(!('@timestamp',desc)))"
  )
  return f"{base_url}/app/discover#/?_g={global_state}&_a={app_state}"


def kibana_generate_link(params: KibanaGenerateLinkInput) -> dict[str, Any]:
  """工具 14：拼装 Kibana Discover 跳转链接（离线，不访问网络）。"""
  tool = "kibana_generate_link"
  try:
    if params.end_time <= params.start_time:
      return {"ok": False, "error": "end_time 必须大于 start_time", "tool": tool}

    if params.end_time - params.start_time > timedelta(hours=MAX_TIME_WINDOW_HOURS):
      return {
        "ok": False,
        "error": f"时间窗口跨度不能超过 {MAX_TIME_WINDOW_HOURS} 小时",
        "tool": tool,
      }

    index_pattern = params.index_pattern.strip()
    if not index_pattern:
      return {"ok": False, "error": "index_pattern 不能为空", "tool": tool}

    base_url = _resolve_kibana_base_url()
    kql_query = _build_kql_query(params.query, params.log_type)
    url = _build_discover_url(
      base_url=base_url,
      index_pattern=index_pattern,
      start_time=params.start_time,
      end_time=params.end_time,
      kql_query=kql_query,
    )
    return {
      "ok": True,
      "url": url,
      "tool": tool,
      "index_pattern": index_pattern,
      "start_time": _to_utc_iso(params.start_time),
      "end_time": _to_utc_iso(params.end_time),
      "query": kql_query,
    }
  except Exception as exc:
    return {"ok": False, "error": str(exc), "tool": tool}
