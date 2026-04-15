from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/status")
def system_status() -> dict:
    return {
        "kafka_bootstrap_servers": settings.kafka_bootstrap_servers,
        "kafka_topic": settings.kafka_topic,
        "elasticsearch_hosts": settings.elasticsearch_hosts,
        "elasticsearch_index_pattern": settings.elasticsearch_index_pattern,
    }
