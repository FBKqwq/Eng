from fastapi import APIRouter
from app.core.config import settings
from app.schemas.system import DockerStatusResponse, SystemStatusResponse
from app.services.docker_status import get_docker_status
from app.services.elasticsearch.cluster_status import get_elasticsearch_health_snapshot
from app.services.kafka.cluster_status import get_kafka_status_snapshot

router = APIRouter()


@router.get("/status", response_model=SystemStatusResponse)
def system_status() -> SystemStatusResponse:
    docker_status = _get_docker_status()

    return SystemStatusResponse(
        kafka_bootstrap_servers=settings.kafka_bootstrap_servers,
        kafka_topic=settings.kafka_topic,
        elasticsearch_hosts=settings.elasticsearch_hosts,
        elasticsearch_index_pattern=settings.elasticsearch_index_pattern,
        kafka=get_kafka_status_snapshot(),
        elasticsearch=get_elasticsearch_health_snapshot(),
        docker=docker_status,
        containers=docker_status.containers,
        services=docker_status.containers,
    )


@router.get("/containers", response_model=DockerStatusResponse)
def system_containers() -> DockerStatusResponse:
    return _get_docker_status()


def _get_docker_status() -> DockerStatusResponse:
    return get_docker_status(
        project_name=settings.docker_project_name,
        monitored_services=settings.docker_monitored_services.split(","),
    )
