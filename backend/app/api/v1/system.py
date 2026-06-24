from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, TypeVar

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.response import ApiResponse, ok_envelope
from app.schemas.system import DockerStatusResponse, PipelineVerifyRequest, PipelineVerifyResponse, SystemStatusResponse
from app.services.docker_status import get_docker_status
from app.services.elasticsearch.cluster_status import get_elasticsearch_health_snapshot
from app.services.kafka.cluster_status import get_kafka_status_snapshot
from app.services.pipeline_verification import run_pipeline_verification


router = APIRouter()


T = TypeVar("T")


def _parallel_snapshot(probes: dict[str, Callable[[], T]]) -> dict[str, T]:
    """并发执行一组探活函数，整体耗时 ≈ 最慢那个而不是累加。"""
    with ThreadPoolExecutor(max_workers=max(len(probes), 1)) as pool:
        futures = {name: pool.submit(fn) for name, fn in probes.items()}
        return {name: future.result() for name, future in futures.items()}


@router.get("/status", response_model=ApiResponse[SystemStatusResponse])
def system_status() -> ApiResponse[SystemStatusResponse]:
    snapshots = _parallel_snapshot(
        {
            "docker": _get_docker_status,
            "kafka": get_kafka_status_snapshot,
            "elasticsearch": get_elasticsearch_health_snapshot,
        }
    )
    docker_status = snapshots["docker"]

    return ok_envelope(
        SystemStatusResponse(
            kafka_bootstrap_servers=settings.kafka_bootstrap_servers,
            kafka_topic=settings.kafka_topic,
            elasticsearch_hosts=settings.elasticsearch_hosts,
            elasticsearch_index_pattern=settings.elasticsearch_index_pattern,
            kafka=snapshots["kafka"],
            elasticsearch=snapshots["elasticsearch"],
            docker=docker_status,
            containers=docker_status.containers,
            services=docker_status.containers,
        )
    )


@router.get("/containers", response_model=ApiResponse[DockerStatusResponse])
def system_containers() -> ApiResponse[DockerStatusResponse]:
    return ok_envelope(_get_docker_status())


@router.post("/pipeline/verify", response_model=ApiResponse[PipelineVerifyResponse])
def verify_pipeline(payload: PipelineVerifyRequest) -> ApiResponse[PipelineVerifyResponse]:
    result = run_pipeline_verification(
        count=payload.count,
        workers=payload.workers,
        kafka_wait=payload.kafka_wait,
        es_wait=payload.es_wait,
    )
    return ok_envelope(result)


def _get_docker_status() -> DockerStatusResponse:
    return get_docker_status(
        project_name=settings.docker_project_name,
        monitored_services=settings.docker_monitored_services.split(","),
    )
