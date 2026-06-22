"""系统健康检查 Agent 工具。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §3.2 工具 9
组合：elasticsearch/cluster_status + kafka/cluster_status + docker_status
"""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.services.docker_status import get_docker_status
from app.services.elasticsearch.cluster_status import get_elasticsearch_health_snapshot
from app.services.kafka.cluster_status import get_kafka_status_snapshot


def system_health_check() -> dict[str, Any]:
  """工具 9：组合 ES / Kafka / Docker 健康快照。"""
  elasticsearch = get_elasticsearch_health_snapshot()
  kafka = get_kafka_status_snapshot()
  docker = get_docker_status(
    project_name=settings.docker_project_name,
    monitored_services=settings.docker_monitored_services.split(","),
  )

  ok = elasticsearch.available and kafka.available and docker.available

  return {
    "ok": ok,
    "tool": "system_health_check",
    "elasticsearch": elasticsearch.model_dump(),
    "kafka": kafka.model_dump(),
    "docker": docker.model_dump(),
  }
