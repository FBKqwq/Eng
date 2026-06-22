"""证据包压缩构建。

职责：原始日志 → 过滤 → 分组 → 采样 → 证据包；控制进入 LLM 的 token 量。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.6
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

# 单条 message 最大字符数，控制进入下游 LLM 的 token 量
_MAX_MESSAGE_CHARS = 500
_TOP_N = 10

_ERROR_LEVELS = frozenset({"ERROR", "CRITICAL"})
_WARN_LEVELS = frozenset({"WARN", "WARNING"})


def build_evidence_package(
    raw_logs: list[dict[str, Any]],
    metrics: dict[str, Any] | None = None,
    *,
    max_logs: int = 50,
) -> dict[str, Any]:
    """将原始日志与聚合指标压缩为受控证据包。"""
    input_log_count = len(raw_logs)
    metrics_out = dict(metrics) if metrics else {}

    if input_log_count == 0:
        return _empty_result(metrics_out)

    normalized_logs = [_normalize_log(log) for log in raw_logs]
    summary = _build_summary(normalized_logs)
    grouped = _build_grouped(normalized_logs)
    samples = _sample_logs(normalized_logs, max_logs=max_logs)

    return {
        "ok": True,
        "evidence_package": {
            "summary": summary,
            "grouped": grouped,
            "samples": samples,
            "metrics": metrics_out,
        },
        "input_log_count": input_log_count,
        "sampled_count": len(samples),
    }


def _empty_result(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "evidence_package": {
            "summary": {
                "total_logs": 0,
                "error_count": 0,
                "warn_count": 0,
                "top_services": [],
                "top_error_codes": [],
            },
            "grouped": {
                "by_service": {},
                "by_error_code": {},
                "by_log_level": {},
            },
            "samples": [],
            "metrics": metrics,
        },
        "input_log_count": 0,
        "sampled_count": 0,
    }


def _normalize_log(log: dict[str, Any]) -> dict[str, Any]:
    """提取关键字段并规范化级别，便于分组与采样。"""
    level = _normalize_level(log.get("log_level"))
    service = _coerce_str(log.get("service_name")) or "unknown-service"
    error_code = _coerce_str(log.get("error_code")) or "_none_"
    return {
        "log_id": _coerce_str(log.get("log_id")),
        "timestamp": log.get("timestamp") or log.get("@timestamp"),
        "log_level": level,
        "log_type": log.get("log_type"),
        "event_type": log.get("event_type"),
        "service_name": service,
        "message": _coerce_str(log.get("message")),
        "error_code": None if error_code == "_none_" else error_code,
        "trace_id": log.get("trace_id"),
        "request_id": log.get("request_id"),
        "status": log.get("status"),
    }


def _normalize_level(level: Any) -> str:
    if level is None:
        return "UNKNOWN"
    text = str(level).strip().upper()
    if text in _WARN_LEVELS:
        return "WARNING"
    return text or "UNKNOWN"


def _coerce_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _is_error_level(level: str) -> bool:
    return level in _ERROR_LEVELS


def _is_warn_level(level: str) -> bool:
    return level in _WARN_LEVELS


def _build_summary(logs: list[dict[str, Any]]) -> dict[str, Any]:
    service_counter: Counter[str] = Counter()
    error_counter: Counter[str] = Counter()
    error_count = 0
    warn_count = 0

    for log in logs:
        service_counter[log["service_name"]] += 1
        if log.get("error_code"):
            error_counter[log["error_code"]] += 1
        level = log["log_level"]
        if _is_error_level(level):
            error_count += 1
        elif _is_warn_level(level):
            warn_count += 1

    return {
        "total_logs": len(logs),
        "error_count": error_count,
        "warn_count": warn_count,
        "top_services": [name for name, _ in service_counter.most_common(_TOP_N)],
        "top_error_codes": [code for code, _ in error_counter.most_common(_TOP_N)],
    }


def _build_grouped(logs: list[dict[str, Any]]) -> dict[str, Any]:
    by_service: Counter[str] = Counter()
    by_error_code: Counter[str] = Counter()
    by_log_level: Counter[str] = Counter()

    for log in logs:
        by_service[log["service_name"]] += 1
        by_log_level[log["log_level"]] += 1
        code = log.get("error_code")
        if code:
            by_error_code[code] += 1

    return {
        "by_service": dict(by_service),
        "by_error_code": dict(by_error_code),
        "by_log_level": dict(by_log_level),
    }


def _group_key(log: dict[str, Any]) -> tuple[str, str, str]:
    code = log.get("error_code") or "_none_"
    return (log["service_name"], code, log["log_level"])


def _sample_logs(logs: list[dict[str, Any]], *, max_logs: int) -> list[dict[str, Any]]:
    """按优先级分层采样：ERROR → WARN → 其余；层内按组轮询取代表样本。"""
    if max_logs <= 0 or not logs:
        return []

    error_logs = [log for log in logs if _is_error_level(log["log_level"])]
    warn_logs = [log for log in logs if _is_warn_level(log["log_level"])]
    other_logs = [
        log
        for log in logs
        if not _is_error_level(log["log_level"]) and not _is_warn_level(log["log_level"])
    ]

    samples: list[dict[str, Any]] = []
    for tier_logs in (error_logs, warn_logs, other_logs):
        if len(samples) >= max_logs:
            break
        remaining = max_logs - len(samples)
        samples.extend(_sample_tier(tier_logs, max_logs=remaining))
    return samples


def _sample_tier(logs: list[dict[str, Any]], *, max_logs: int) -> list[dict[str, Any]]:
    """单层内按 (service, error_code, level) 分组后轮询采样。"""
    if max_logs <= 0 or not logs:
        return []

    buckets: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for log in logs:
        buckets[_group_key(log)].append(log)

    ordered_buckets = sorted(
        buckets.items(),
        key=lambda item: (-len(item[1]), item[0]),
    )

    for _, entries in ordered_buckets:
        entries.sort(key=lambda item: str(item.get("timestamp") or ""))

    samples: list[dict[str, Any]] = []
    indices = [0] * len(ordered_buckets)

    while len(samples) < max_logs:
        progressed = False
        for idx, (_, entries) in enumerate(ordered_buckets):
            if indices[idx] < len(entries):
                samples.append(_trim_sample(entries[indices[idx]]))
                indices[idx] += 1
                progressed = True
                if len(samples) >= max_logs:
                    break
        if not progressed:
            break

    return samples


def _trim_sample(log: dict[str, Any]) -> dict[str, Any]:
    """裁剪样本字段，截断过长 message。"""
    message = log.get("message") or ""
    if len(message) > _MAX_MESSAGE_CHARS:
        message = message[:_MAX_MESSAGE_CHARS] + "…"

    sample: dict[str, Any] = {
        "log_id": log.get("log_id"),
        "timestamp": log.get("timestamp"),
        "service_name": log.get("service_name"),
        "log_level": log.get("log_level"),
        "event_type": log.get("event_type"),
        "message": message,
    }
    if log.get("error_code"):
        sample["error_code"] = log["error_code"]
    if log.get("trace_id"):
        sample["trace_id"] = log["trace_id"]
    if log.get("request_id"):
        sample["request_id"] = log["request_id"]
    if log.get("status") is not None:
        sample["status"] = log["status"]
    return sample
