import json
from typing import Optional

from kafka import KafkaProducer
from kafka.errors import KafkaError

from app.core.config import settings


def get_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        retries=3,
        request_timeout_ms=30_000,
    )


def send_log_message(
    message: dict,
    *,
    producer: Optional[KafkaProducer] = None,
    topic: Optional[str] = None,
) -> dict:
    """
    发送一条日志到 Kafka。
    若传入 producer 则复用连接；否则创建临时 producer 并在发送后关闭。
    """
    own_producer = producer is None
    if own_producer:
        producer = get_producer()
    target_topic = topic or settings.kafka_topic
    try:
        producer.send(target_topic, message)
        producer.flush()
        return {"topic": target_topic, "sent": True, "message": message}
    except KafkaError as exc:
        raise RuntimeError(
            f"Kafka 发送失败: bootstrap={settings.kafka_bootstrap_servers!r}, "
            f"topic={target_topic!r}, error={exc!s}"
        ) from exc
    finally:
        if own_producer and producer is not None:
            producer.close()
