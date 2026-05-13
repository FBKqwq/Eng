from typing import Any, Optional

from app.core.config import settings
from app.schemas.system import ElasticsearchHealthSnapshot
from app.services.elasticsearch.client import get_es_client


ES_STATUS_TIMEOUT_SECONDS = 3


def get_elasticsearch_health_snapshot() -> ElasticsearchHealthSnapshot:
    hosts = _split_csv(settings.elasticsearch_hosts)

    try:
        client = get_es_client().options(request_timeout=ES_STATUS_TIMEOUT_SECONDS)
        info = dict(client.info())
        health = dict(client.cluster.health())
        index_summary = _safe_index_summary(client)

        return ElasticsearchHealthSnapshot(
            hosts=hosts,
            index_pattern=settings.elasticsearch_index_pattern,
            available=True,
            cluster_status=str(health.get("status", "unknown")),
            cluster_name=health.get("cluster_name") or info.get("cluster_name"),
            node_name=info.get("name"),
            version=(info.get("version") or {}).get("number"),
            number_of_nodes=_to_int(health.get("number_of_nodes")),
            number_of_data_nodes=_to_int(health.get("number_of_data_nodes")),
            active_shards=_to_int(health.get("active_shards")),
            relocating_shards=_to_int(health.get("relocating_shards")),
            initializing_shards=_to_int(health.get("initializing_shards")),
            unassigned_shards=_to_int(health.get("unassigned_shards")),
            timed_out=bool(health.get("timed_out")) if health.get("timed_out") is not None else None,
            indices_count=index_summary.get("indices_count"),
            docs_count=index_summary.get("docs_count"),
        )
    except Exception as exc:
        return ElasticsearchHealthSnapshot(
            hosts=hosts,
            index_pattern=settings.elasticsearch_index_pattern,
            available=False,
            cluster_status="unknown",
            error=str(exc),
        )


def _safe_index_summary(client: Any) -> dict[str, Optional[int]]:
    return {
        "indices_count": _safe_indices_count(client),
        "docs_count": _safe_docs_count(client),
    }


def _safe_indices_count(client: Any) -> Optional[int]:
    try:
        response = dict(
            client.indices.get(
                index=settings.elasticsearch_index_pattern,
                ignore_unavailable=True,
                allow_no_indices=True,
            )
        )
        return len(response)
    except Exception:
        return None


def _safe_docs_count(client: Any) -> Optional[int]:
    try:
        response = dict(
            client.count(
                index=settings.elasticsearch_index_pattern,
                ignore_unavailable=True,
                allow_no_indices=True,
            )
        )
        return _to_int(response.get("count"))
    except Exception:
        return None


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
