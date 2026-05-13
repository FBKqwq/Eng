import json
import subprocess
from typing import Dict, Iterable, Optional

from app.schemas.system import ContainerStatus, DockerStatusResponse


DOCKER_TIMEOUT_SECONDS = 8


def get_docker_status(project_name: str, monitored_services: Iterable[str]) -> DockerStatusResponse:
    services = [service.strip() for service in monitored_services if service.strip()]

    try:
        containers = _read_compose_containers(project_name)
        stats = _read_container_stats()
    except (FileNotFoundError, subprocess.SubprocessError, OSError, json.JSONDecodeError) as exc:
        return DockerStatusResponse(
            project=project_name,
            available=False,
            error=str(exc),
            containers={service: _unknown_container(service, f"Docker status unavailable: {exc}") for service in services},
        )

    by_service = {
        _resolve_service_name(container, project_name): container
        for container in containers
    }

    result: Dict[str, ContainerStatus] = {}
    for service in services:
        container = by_service.get(service)
        if not container:
            result[service] = _unknown_container(service, "Container not found in Docker project")
            continue

        name = container.get("Names", "")
        stat = stats.get(name) or stats.get(container.get("ID", ""))
        result[service] = _build_container_status(service, container, stat)

    return DockerStatusResponse(project=project_name, available=True, containers=result)


def _read_compose_containers(project_name: str) -> list[dict]:
    return _run_json_lines(
        [
            "docker",
            "ps",
            "-a",
            "--filter",
            f"label=com.docker.compose.project={project_name}",
            "--format",
            "{{json .}}",
        ]
    )


def _read_container_stats() -> dict[str, dict]:
    stats = _run_json_lines(["docker", "stats", "--no-stream", "--format", "{{json .}}"])
    by_key: dict[str, dict] = {}
    for item in stats:
        if item.get("Name"):
            by_key[item["Name"]] = item
        if item.get("ID"):
            by_key[item["ID"]] = item
    return by_key


def _run_json_lines(command: list[str]) -> list[dict]:
    completed = subprocess.run(
        command,
        capture_output=True,
        check=True,
        encoding="utf-8",
        errors="replace",
        timeout=DOCKER_TIMEOUT_SECONDS,
    )

    return [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]


def _resolve_service_name(container: dict, project_name: str) -> str:
    name = container.get("Names", "")
    if name.startswith(f"{project_name}-") and name.endswith("-1"):
        return name[len(project_name) + 1 : -2]
    if name.endswith("-1"):
        return name[:-2]
    return name


def _build_container_status(service: str, container: dict, stat: Optional[dict]) -> ContainerStatus:
    raw_state = container.get("State")
    status = "running" if raw_state == "running" else "down"
    name = container.get("Names", service)

    return ContainerStatus(
        name=name,
        service=service,
        status=status,
        raw_state=raw_state,
        raw_status=container.get("Status"),
        image=container.get("Image"),
        container_id=container.get("ID"),
        ports=container.get("Ports") or None,
        endpoint=_first_port_mapping(container.get("Ports")),
        cpu_percent=stat.get("CPUPerc") if stat else None,
        memory_usage=stat.get("MemUsage") if stat else None,
        memory_percent=stat.get("MemPerc") if stat else None,
        network_io=stat.get("NetIO") if stat else None,
        block_io=stat.get("BlockIO") if stat else None,
        pids=stat.get("PIDs") if stat else None,
        detail=container.get("Status"),
    )


def _first_port_mapping(ports: Optional[str]) -> Optional[str]:
    if not ports:
        return None

    first_port = ports.split(",")[0].strip()
    return first_port or None


def _unknown_container(service: str, detail: str) -> ContainerStatus:
    return ContainerStatus(
        name=service,
        service=service,
        status="unknown",
        detail=detail,
    )
