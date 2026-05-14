"""Kafka 业务 topic 预建，避免仅依赖 broker 自动建 topic 开关。"""

from __future__ import annotations

from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError

from app.core.config import settings

_ADMIN_TIMEOUT_MS = 8000


def ensure_configured_topic(
    *,
    num_partitions: int | None = None,
    replication_factor: int | None = None,
) -> dict:
    """若配置的 topic 不存在则创建；已存在则 noop。供日志生产任务启动时调用。"""
    partitions = num_partitions if num_partitions is not None else 3
    replicas = replication_factor if replication_factor is not None else 1
    bootstrap = [s.strip() for s in settings.kafka_bootstrap_servers.split(",") if s.strip()]
    topic = settings.kafka_topic

    admin = KafkaAdminClient(
        bootstrap_servers=bootstrap,
        client_id="elk-backend-topic-setup",
        request_timeout_ms=_ADMIN_TIMEOUT_MS,
        api_version_auto_timeout_ms=_ADMIN_TIMEOUT_MS,
    )
    try:
        existing = set(admin.list_topics())
        if topic in existing:
            return {"topic": topic, "created": False, "reason": "already_exists"}

        admin.create_topics(
            new_topics=[
                NewTopic(
                    name=topic,
                    num_partitions=partitions,
                    replication_factor=replicas,
                )
            ],
            validate_only=False,
        )
        return {"topic": topic, "created": True, "partitions": partitions, "replication_factor": replicas}
    except TopicAlreadyExistsError:
        return {"topic": topic, "created": False, "reason": "already_exists_race"}
    finally:
        admin.close()
