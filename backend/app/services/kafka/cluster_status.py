from kafka import KafkaAdminClient

from app.core.config import settings
from app.schemas.system import KafkaStatusSnapshot, KafkaTopicSnapshot


KAFKA_STATUS_TIMEOUT_MS = 3000


def get_kafka_status_snapshot() -> KafkaStatusSnapshot:
    bootstrap_servers = _split_csv(settings.kafka_bootstrap_servers)

    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            client_id="elk-backend-status-snapshot",
            request_timeout_ms=KAFKA_STATUS_TIMEOUT_MS,
            api_version_auto_timeout_ms=KAFKA_STATUS_TIMEOUT_MS,
        )
        try:
            topics = sorted(admin_client.list_topics())
            topic_snapshot = _describe_configured_topic(admin_client, topics)
            brokers_count = len(getattr(admin_client, "_client").cluster.brokers())
        finally:
            admin_client.close()

        return KafkaStatusSnapshot(
            bootstrap_servers=bootstrap_servers,
            topic=settings.kafka_topic,
            available=True,
            brokers_count=brokers_count,
            topics_count=len(topics),
            configured_topic=topic_snapshot,
        )
    except Exception as exc:
        return KafkaStatusSnapshot(
            bootstrap_servers=bootstrap_servers,
            topic=settings.kafka_topic,
            available=False,
            configured_topic=KafkaTopicSnapshot(name=settings.kafka_topic, exists=False),
            error=str(exc),
        )


def _describe_configured_topic(admin_client: KafkaAdminClient, topics: list[str]) -> KafkaTopicSnapshot:
    if settings.kafka_topic not in topics:
        return KafkaTopicSnapshot(name=settings.kafka_topic, exists=False)

    topic_descriptions = admin_client.describe_topics([settings.kafka_topic])
    partitions = topic_descriptions[0].get("partitions", []) if topic_descriptions else []
    replication_factor = len(partitions[0].get("replicas", [])) if partitions else None

    return KafkaTopicSnapshot(
        name=settings.kafka_topic,
        exists=True,
        partitions=len(partitions),
        replication_factor=replication_factor,
    )


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]
