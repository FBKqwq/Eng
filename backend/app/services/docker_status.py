import json
import socket
import subprocess
from typing import Dict, Iterable, Optional
from urllib.parse import urlparse

from app.core.config import settings
from app.schemas.system import ContainerStatus, DockerStatusResponse


DOCKER_TIMEOUT_SECONDS = 8
GATEWAY_PROBE_TIMEOUT_SECONDS = 2.5


def get_docker_status(project_name: str, monitored_services: Iterable[str]) -> DockerStatusResponse:
    services = [service.strip() for service in monitored_services if service.strip()]
    fallback_error: str | None = None

    try:
        containers = _read_compose_containers(project_name)
        stats = _read_container_stats()
    except Exception as exc:  # noqa: BLE001
        containers = []
        stats = {}
        fallback_error = f"Docker status unavailable: {exc}"

    by_service = {
        _resolve_service_name(container, project_name): container
        for container in containers
    }

    result: Dict[str, ContainerStatus] = {}
    docker_available = containers and stats

    for service in services:
        try:
            if docker_available:
                container = by_service.get(service)
                if not container:
                    probe = _gateway_probe_container(service)
                    result[service] = probe or _unknown_container(
                        service,
                        "Container not found in Docker project",
                    )
                    continue

                name = container.get("Names", "")
                stat = stats.get(name) or stats.get(container.get("ID", ""))
                result[service] = _build_container_status(service, container, stat)
            else:
                probe = _gateway_probe_container(service)
                result[service] = probe or _unknown_container(
                    service,
                    "Docker status unavailable and no gateway probe configured",
                )
        except Exception as exc:  # noqa: BLE001
            result[service] = _unknown_container(service, f"Docker status parse failed: {exc}")

    return DockerStatusResponse(
        project=project_name,
        available=any(item.status == "running" for item in result.values()),
        error=fallback_error,
        containers=result,
    )


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


def _build_gateway_probe_statuses(services: Iterable[str]) -> dict[str, ContainerStatus]:
    return {
        service: _safe_gateway_probe_container(service)
        for service in services
    }


def _safe_gateway_probe_container(service: str) -> ContainerStatus:
    try:
        return _gateway_probe_container(service) or _unknown_container(
            service,
            "Docker status unavailable and no gateway probe is configured",
        )
    except Exception as exc:  # noqa: BLE001
        return _unknown_container(service, f"Gateway probe failed: {exc}")


def _gateway_probe_container(service: str) -> Optional[ContainerStatus]:
    endpoint = _gateway_probe_endpoint(service)
    if not endpoint:
        return None

    host, port = endpoint
    ok, error = _tcp_probe(host, port)
    target = f"{host}:{port}"
    status = "running" if ok else "down"
    detail = f"Gateway TCP probe {'succeeded' if ok else 'failed'}: {target}"
    if error:
        detail = f"{detail}; {error}"

    return ContainerStatus(
        name=f"gateway-{service}",
        service=service,
        status=status,
        raw_state="remote_probe",
        raw_status=detail,
        endpoint=target,
        detail=detail,
    )


def _gateway_probe_endpoint(service: str) -> Optional[tuple[str, int]]:
    if service == "kafka":
        return _host_port_from_bootstrap(getattr(settings, "kafka_bootstrap_servers", ""), default_port=9092)
    if service == "elasticsearch":
        return _host_port_from_url(getattr(settings, "elasticsearch_hosts", ""), default_port=9200)
    if service == "kibana":
        return _host_port_from_url(getattr(settings, "kibana_base_url", ""), default_port=5601)
    if service == "logstash":
        return _host_port_from_url(getattr(settings, "logstash_hosts", ""), default_port=9600)
    return None


def _host_port_from_bootstrap(value: str, *, default_port: int) -> Optional[tuple[str, int]]:
    first = next((item.strip() for item in value.split(",") if item.strip()), "")
    if not first:
        return None
    if "://" in first:
        return _host_port_from_url(first, default_port=default_port)
    if first.startswith("[") and "]" in first:
        host, _, rest = first[1:].partition("]")
        port_text = rest[1:] if rest.startswith(":") else ""
    else:
        host, _, port_text = first.rpartition(":")
        if not host:
            host, port_text = first, ""
    return _normalize_host_port(host, port_text, default_port=default_port)


def _host_port_from_url(value: str, *, default_port: int) -> Optional[tuple[str, int]]:
    first = next((item.strip() for item in value.split(",") if item.strip()), "")
    if not first:
        return None
    parsed = urlparse(first if "://" in first else f"http://{first}")
    try:
        port_text = str(parsed.port or "")
    except ValueError:
        port_text = ""
    return _normalize_host_port(parsed.hostname or "", port_text, default_port=default_port)


def _normalize_host_port(host: str, port_text: str, *, default_port: int) -> Optional[tuple[str, int]]:
    normalized_host = host.strip()
    if not normalized_host:
        return None
    try:
        port = int(port_text) if port_text else default_port
    except ValueError:
        port = default_port
    return normalized_host, port


def _tcp_probe(host: str, port: int) -> tuple[bool, Optional[str]]:
    try:
        with socket.create_connection((host, port), timeout=GATEWAY_PROBE_TIMEOUT_SECONDS):
            return True, None
    except OSError as exc:
        return False, str(exc)
