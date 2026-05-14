import json
from kafka import KafkaProducer
from app.core.config import settings


def get_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        retries=3,
    )


def send_log_message(message: dict) -> dict:
    producer = get_producer()
    producer.send(settings.kafka_topic, message)
    producer.flush()
    producer.close()
    return {"topic": settings.kafka_topic, "sent": True, "message": message}
