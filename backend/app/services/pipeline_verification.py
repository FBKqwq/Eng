from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from app.schemas.system import PipelineVerifyNode, PipelineVerifyResponse


NODE_LABELS = {
    "producer": "日志生产",
    "kafka": "Kafka 接收",
    "logstash": "Logstash 处理",
    "elasticsearch": "Elasticsearch 检索",
}


def run_pipeline_verification(
    *,
    count: int = 2,
    workers: int = 2,
    kafka_wait: float = 45.0,
    es_wait: float = 120.0,
) -> PipelineVerifyResponse:
    backend_root = Path(__file__).resolve().parents[2]
    command = [
        sys.executable,
        "-m",
        "app.tasks.verify_log_pipeline_full",
        "--count",
        str(count),
        "--workers",
        str(workers),
        "--kafka-wait",
        str(kafka_wait),
        "--es-wait",
        str(es_wait),
    ]
    started = time.perf_counter()

    try:
        completed = subprocess.run(
            command,
            cwd=backend_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=kafka_wait + es_wait + 30,
            check=False,
        )
        duration_ms = int((time.perf_counter() - started) * 1000)
        output = completed.stdout + "\n" + completed.stderr

        return PipelineVerifyResponse(
            success=completed.returncode == 0,
            exit_code=completed.returncode,
            duration_ms=duration_ms,
            command=command,
            nodes=_build_nodes(completed.returncode, output),
            stdout=completed.stdout,
            stderr=completed.stderr,
            error=None if completed.returncode == 0 else _error_summary(completed.returncode, output),
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        stdout = _decode_timeout_output(exc.stdout)
        stderr = _decode_timeout_output(exc.stderr)
        output = stdout + "\n" + stderr
        return PipelineVerifyResponse(
            success=False,
            exit_code=124,
            duration_ms=duration_ms,
            command=command,
            nodes=_build_nodes(124, output),
            stdout=stdout,
            stderr=stderr,
            error="全链路验证超时，请检查 Kafka、Logstash 或 Elasticsearch 写入链路。",
        )


def _build_nodes(exit_code: int, output: str) -> list[PipelineVerifyNode]:
    generated = "[1]" in output and "模拟生成" in output
    multi_threaded = "多线程生产完成" in output or "worker[" in output
    sent_to_kafka = "[2]" in output and "Kafka Producer" in output
    consumed_from_kafka = "[3] Kafka Consumer" in output
    es_hit = "[4->5] ES 命中" in output

    producer_status = "success" if generated and exit_code != 4 else _status_for_failure(exit_code, {4})
    kafka_status = "success" if sent_to_kafka and consumed_from_kafka else _status_for_failure(exit_code, {2, 3, 5})
    logstash_status = "success" if es_hit else _status_for_failure(exit_code, {7, 124})
    es_status = "success" if es_hit else _status_for_failure(exit_code, {6, 7, 124})

    if exit_code == 0:
        logstash_status = "success"
        es_status = "success"

    return [
        PipelineVerifyNode(
            key="producer",
            label=NODE_LABELS["producer"],
            status=producer_status,
            detail=_detail("多线程生成结构化 dict", generated and multi_threaded),
        ),
        PipelineVerifyNode(
            key="kafka",
            label=NODE_LABELS["kafka"],
            status=kafka_status,
            detail=_detail("Producer 写入并被 Consumer 读回", consumed_from_kafka),
        ),
        PipelineVerifyNode(
            key="logstash",
            label=NODE_LABELS["logstash"],
            status=logstash_status,
            detail=_detail("消费 Kafka 并写入 app-logs-*", es_hit),
        ),
        PipelineVerifyNode(
            key="elasticsearch",
            label=NODE_LABELS["elasticsearch"],
            status=es_status,
            detail=_detail("按 log_id 检索命中", es_hit),
        ),
    ]


def _status_for_failure(exit_code: int, failed_codes: set[int]) -> str:
    if exit_code in failed_codes:
        return "failed"
    if exit_code == 0:
        return "success"
    return "pending"


def _detail(text: str, ok: bool) -> str:
    return f"{text}：{'通过' if ok else '未确认'}"


def _error_summary(exit_code: int, output: str) -> str:
    for line in reversed([x.strip() for x in output.splitlines() if x.strip()]):
        if "[错误]" in line or "[FAIL]" in line or "Traceback" in line:
            return line
    return f"全链路验证失败，exit_code={exit_code}"


def _decode_timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
