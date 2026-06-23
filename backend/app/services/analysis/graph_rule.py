"""规则任务子图（最小版）。

职责：关键错误即时深挖；由 trigger_scanner 周期扫描触发。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.5

节点流：parse_trigger_event -> fetch_context -> correlate_events -> build_evidence
       -> infer_root_cause -> assess_severity -> generate_event_report
"""

from __future__ import annotations

import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

from langgraph.graph import END, StateGraph

from app.services.analysis.schemas import normalize_trigger
from app.services.analysis.state import (
    AnalysisState,
    append_node_trace,
    create_initial_state,
    record_error,
)
from app.services.diagnosis.rule_engine import match_log
from app.services.elasticsearch.context_service import (
    get_service_window,
    get_similar_errors,
    get_trace_context,
)
from app.services.langchain.diagnosis_chain import generate_event_report, infer_root_cause
from app.services.langchain.evidence_builder import build_evidence_package

_NODE_ORDER: tuple[str, ...] = (
    "parse_trigger_event",
    "fetch_context",
    "correlate_events",
    "build_evidence",
    "infer_root_cause",
    "assess_severity",
    "generate_event_report",
)

_SEVERITY_RANK: dict[str, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}

_RANK_TO_SEVERITY: dict[int, str] = {v: k for k, v in _SEVERITY_RANK.items()}

_CONTEXT_LIMIT = 50
_CONTEXT_WINDOW_BEFORE_MINUTES = 15
_CONTEXT_WINDOW_AFTER_MINUTES = 5


def build_rule_graph() -> Any:
    """构建并编译规则子图（LangGraph StateGraph）。"""
    return _compile_rule_graph()


def run_rule_subgraph(trigger_event: dict[str, Any]) -> dict[str, Any]:
    """执行规则子图；不负责持久化（由 trigger_scanner 写库 + 去重）。"""
    trigger_raw: dict[str, Any] = {
        "trigger_type": "rule",
        "trigger_event": trigger_event,
    }
    normalized = normalize_trigger(trigger_raw)
    if not normalized.get("ok"):
        error_msg = str(normalized.get("error") or "invalid trigger")
        return {
            "ok": False,
            "report": {},
            "alert_candidate": {},
            "node_trace": [],
            "errors": [
                {
                    "node_name": "normalize_trigger",
                    "message": error_msg,
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                }
            ],
        }

    trigger = normalized["trigger"]
    event = dict(trigger.get("trigger_event") or {})
    time_window = _derive_context_window(event)

    state = create_initial_state(
        "rule",
        trigger_event=event,
        time_window=time_window,
    )
    # create_initial_state 复用模块级空容器，需重置以免多次运行污染各列表/字典字段
    state["node_trace"] = []
    state["errors"] = []
    state["raw_logs"] = []
    state["metrics"] = {}
    state["query_plan"] = {}
    state["relations"] = []
    state["evidence_package"] = {}
    state["analysis_report"] = {}
    state["alert_candidate"] = {}

    graph = build_rule_graph()
    final_state: AnalysisState = graph.invoke(state)

    report = final_state.get("analysis_report") or {}
    alert_candidate = final_state.get("alert_candidate") or {}
    return {
        "ok": bool(report),
        "report": report,
        "alert_candidate": alert_candidate,
        "node_trace": list(final_state.get("node_trace") or []),
        "errors": list(final_state.get("errors") or []),
    }


@lru_cache(maxsize=1)
def _compile_rule_graph() -> Any:
    graph = StateGraph(AnalysisState)
    graph.add_node("parse_trigger_event", _node_parse_trigger_event)
    graph.add_node("fetch_context", _node_fetch_context)
    graph.add_node("correlate_events", _node_correlate_events)
    graph.add_node("build_evidence", _node_build_evidence)
    graph.add_node("infer_root_cause", _node_infer_root_cause)
    graph.add_node("assess_severity", _node_assess_severity)
    graph.add_node("generate_event_report", _node_generate_event_report)

    graph.set_entry_point("parse_trigger_event")
    for current, nxt in zip(_NODE_ORDER, _NODE_ORDER[1:], strict=False):
        graph.add_edge(current, nxt)
    graph.add_edge("generate_event_report", END)
    return graph.compile()


def _node_parse_trigger_event(state: AnalysisState) -> dict[str, Any]:
    node = "parse_trigger_event"
    started = time.perf_counter()
    event = dict(state.get("trigger_event") or {})

    try:
        match_result = match_log(event)
        plan = dict(state.get("query_plan") or {})
        plan["rule_match"] = match_result
        state["query_plan"] = plan

        if not match_result.get("ok"):
            raise ValueError(match_result.get("error") or "规则匹配失败")
        if not match_result.get("matched"):
            record_error(state, node, "触发日志未命中任何规则，将以降级模式继续深挖")
        elif not match_result.get("trigger_subgraph"):
            record_error(state, node, "命中规则未标记 trigger_subgraph，将以降级模式继续")

        matched = bool(match_result.get("matched"))
        rule_name = match_result.get("rule_name") or "未命中"
        append_node_trace(
            state,
            node,
            "success",
            duration_ms=_elapsed_ms(started),
            output_summary=f"{'命中' if matched else '未命中'} · {rule_name}",
        )
    except Exception as exc:  # noqa: BLE001 - 节点级降级，不中断整图
        record_error(state, node, str(exc))
        state.setdefault("query_plan", {})["rule_match"] = {
            "ok": False,
            "matched": False,
            "error": str(exc),
        }
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(state, "query_plan", "node_trace", "errors")


def _node_fetch_context(state: AnalysisState) -> dict[str, Any]:
    node = "fetch_context"
    started = time.perf_counter()
    event = dict(state.get("trigger_event") or {})
    window = dict(state.get("time_window") or {})
    start_dt = _parse_iso_datetime(window.get("start"))
    end_dt = _parse_iso_datetime(window.get("end"))

    trace_id = _coerce_str(event.get("trace_id"))
    service = _coerce_str(event.get("service_name"))
    error_code = _coerce_str(event.get("error_code"))

    context_bundle: dict[str, Any] = {
        "trace_context": {},
        "service_window": {},
        "similar_errors": {},
    }
    collected: list[dict[str, Any]] = [_normalize_trigger_log(event)]
    failed_sources: list[str] = []

    try:
        if start_dt is None or end_dt is None:
            raise ValueError("上下文时间窗口不可用")

        if trace_id:
            trace_result = get_trace_context(trace_id, limit=_CONTEXT_LIMIT)
            context_bundle["trace_context"] = trace_result
            if trace_result.get("available"):
                collected.extend(trace_result.get("items") or [])
            else:
                failed_sources.append("trace_context")
                record_error(
                    state,
                    node,
                    f"trace 上下文不可用: {trace_result.get('error') or 'ES 不可用'}",
                )
        else:
            record_error(state, node, "触发日志缺少 trace_id，跳过 trace 上下文查询")

        if service:
            service_result = get_service_window(
                service, start_dt, end_dt, limit=_CONTEXT_LIMIT
            )
            context_bundle["service_window"] = service_result
            if service_result.get("available"):
                collected.extend(service_result.get("items") or [])
            else:
                failed_sources.append("service_window")
                record_error(
                    state,
                    node,
                    f"服务窗口不可用: {service_result.get('error') or 'ES 不可用'}",
                )
        else:
            record_error(state, node, "触发日志缺少 service_name，跳过服务窗口查询")

        if error_code:
            similar_result = get_similar_errors(
                error_code, start_dt, end_dt, limit=_CONTEXT_LIMIT
            )
            context_bundle["similar_errors"] = similar_result
            if similar_result.get("available"):
                collected.extend(similar_result.get("items") or [])
            else:
                failed_sources.append("similar_errors")
                record_error(
                    state,
                    node,
                    f"同类错误不可用: {similar_result.get('error') or 'ES 不可用'}",
                )
        else:
            record_error(state, node, "触发日志缺少 error_code，跳过同类错误查询")

        plan = dict(state.get("query_plan") or {})
        plan["context_bundle"] = context_bundle
        state["query_plan"] = plan
        state["raw_logs"] = _dedupe_logs(collected)

        append_node_trace(
            state,
            node,
            "success",
            duration_ms=_elapsed_ms(started),
            output_summary=(
                f"采集 {len(state['raw_logs'])} 条"
                + (f"，{len(failed_sources)} 路降级" if failed_sources else "")
            ),
        )
    except Exception as exc:  # noqa: BLE001
        record_error(state, node, str(exc))
        plan = dict(state.get("query_plan") or {})
        plan["context_bundle"] = context_bundle
        state["query_plan"] = plan
        state["raw_logs"] = _dedupe_logs(collected)
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(state, "raw_logs", "query_plan", "node_trace", "errors")


def _node_correlate_events(state: AnalysisState) -> dict[str, Any]:
    node = "correlate_events"
    started = time.perf_counter()

    try:
        logs = list(state.get("raw_logs") or [])
        sorted_logs = sorted(
            logs,
            key=lambda item: _parse_iso_datetime(item.get("timestamp"))
            or datetime.min,
        )

        service_counter: Counter[str] = Counter()
        error_code_counter: Counter[str] = Counter()
        level_counter: Counter[str] = Counter()
        timeline: list[dict[str, Any]] = []

        for log in sorted_logs:
            service = _coerce_str(log.get("service_name")) or "unknown-service"
            code = _coerce_str(log.get("error_code")) or "_none_"
            level = _coerce_str(log.get("log_level")) or "INFO"
            service_counter[service] += 1
            error_code_counter[code] += 1
            level_counter[level] += 1
            timeline.append(
                {
                    "timestamp": log.get("timestamp"),
                    "service_name": service,
                    "error_code": code,
                    "log_level": level,
                    "trace_id": log.get("trace_id"),
                    "log_id": log.get("log_id"),
                }
            )

        cross_service = [
            {"service_name": svc, "count": cnt}
            for svc, cnt in service_counter.most_common(10)
        ]
        relations = [
            {
                "relation_type": "timeline",
                "events": timeline[:30],
            },
            {
                "relation_type": "cross_service",
                "services": cross_service,
            },
        ]

        metrics = dict(state.get("metrics") or {})
        metrics["correlation"] = {
            "total_events": len(sorted_logs),
            "service_count": len(service_counter),
            "top_services": cross_service[:5],
            "top_error_codes": [
                {"error_code": code, "count": cnt}
                for code, cnt in error_code_counter.most_common(5)
            ],
            "level_distribution": dict(level_counter),
        }

        state["relations"] = relations
        state["metrics"] = metrics
        append_node_trace(
            state,
            node,
            "success",
            duration_ms=_elapsed_ms(started),
            output_summary=f"关联 {len(sorted_logs)} 条 · {len(service_counter)} 服务",
        )
    except Exception as exc:  # noqa: BLE001
        record_error(state, node, str(exc))
        state.setdefault("relations", [])
        state.setdefault("metrics", {})["correlation"] = {"total_events": 0}
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(state, "relations", "metrics", "node_trace", "errors")


def _node_build_evidence(state: AnalysisState) -> dict[str, Any]:
    node = "build_evidence"
    started = time.perf_counter()
    try:
        result = build_evidence_package(
            list(state.get("raw_logs") or []),
            dict(state.get("metrics") or {}),
        )
        package = result.get("evidence_package") or {}
        state["evidence_package"] = package
        append_node_trace(
            state,
            node,
            "success",
            duration_ms=_elapsed_ms(started),
            output_summary=(
                f"输入 {result.get('input_log_count', 0)} 条，"
                f"采样 {result.get('sampled_count', 0)} 条"
            ),
        )
    except Exception as exc:  # noqa: BLE001
        record_error(state, node, str(exc))
        state["evidence_package"] = {
            "summary": {"total_logs": 0, "error_count": 0, "warn_count": 0},
            "grouped": {},
            "samples": [],
            "metrics": dict(state.get("metrics") or {}),
        }
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(state, "evidence_package", "node_trace", "errors")


def _node_infer_root_cause(state: AnalysisState) -> dict[str, Any]:
    node = "infer_root_cause"
    started = time.perf_counter()
    try:
        diagnosis = infer_root_cause(dict(state.get("evidence_package") or {}))
        plan = dict(state.get("query_plan") or {})
        plan["root_cause_diagnosis"] = diagnosis
        state["query_plan"] = plan

        degraded = bool(diagnosis.get("degraded"))
        append_node_trace(
            state,
            node,
            "success",
            duration_ms=_elapsed_ms(started),
            output_summary="降级规则根因" if degraded else "根因推断完成",
        )
    except Exception as exc:  # noqa: BLE001
        record_error(state, node, str(exc))
        plan = dict(state.get("query_plan") or {})
        plan["root_cause_diagnosis"] = {
            "ok": False,
            "degraded": True,
            "root_cause": "根因推断失败，请人工复核证据包",
            "confidence": 0.0,
            "severity": "medium",
            "affected_services": [],
            "evidence_refs": [],
            "action_suggestions": ["检查 LLM 配置与证据包内容"],
        }
        state["query_plan"] = plan
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(state, "query_plan", "node_trace", "errors")


def _node_assess_severity(state: AnalysisState) -> dict[str, Any]:
    node = "assess_severity"
    started = time.perf_counter()
    event = dict(state.get("trigger_event") or {})
    plan = dict(state.get("query_plan") or {})
    match_result = plan.get("rule_match") or {}
    diagnosis = plan.get("root_cause_diagnosis") or {}

    try:
        rule_severity = _coerce_str(match_result.get("severity")) or "medium"
        final_severity = _synthesize_severity(rule_severity, diagnosis)
        plan["severity_assessment"] = {
            "rule_severity": rule_severity,
            "llm_severity": diagnosis.get("severity"),
            "llm_confidence": diagnosis.get("confidence"),
            "final_severity": final_severity,
        }
        state["query_plan"] = plan

        service = _coerce_str(event.get("service_name")) or (
            (diagnosis.get("affected_services") or ["unknown-service"])[0]
        )
        error_code = _coerce_str(event.get("error_code")) or "unknown_error"
        rule_id = _coerce_str(match_result.get("rule_id")) or error_code.lower()

        state["alert_candidate"] = {
            "alert_type": error_code.lower(),
            "severity": final_severity,
            "title": _build_alert_title(event, diagnosis, match_result),
            "affected_service": service,
            "description": _coerce_str(diagnosis.get("root_cause"))
            or f"{service} 出现 {error_code} 异常",
            "created_at": _resolve_event_timestamp(event),
            "trigger_log_id": event.get("log_id"),
            "rule_id": rule_id,
            "payload": {
                "error_code": error_code,
                "trace_id": event.get("trace_id"),
                "rule_name": match_result.get("rule_name"),
                "confidence": diagnosis.get("confidence"),
                "evidence_refs": diagnosis.get("evidence_refs") or [],
            },
        }

        append_node_trace(
            state,
            node,
            "success",
            duration_ms=_elapsed_ms(started),
            output_summary=f"定级 {final_severity}（规则 {rule_severity}）",
        )
    except Exception as exc:  # noqa: BLE001
        record_error(state, node, str(exc))
        state["alert_candidate"] = {
            "alert_type": _coerce_str(event.get("error_code")).lower() or "unknown",
            "severity": "medium",
            "title": "事件预警（定级降级）",
            "affected_service": _coerce_str(event.get("service_name")) or "unknown-service",
            "description": str(exc),
            "created_at": _resolve_event_timestamp(event),
            "trigger_log_id": event.get("log_id"),
        }
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(state, "alert_candidate", "query_plan", "node_trace", "errors")


def _node_generate_event_report(state: AnalysisState) -> dict[str, Any]:
    node = "generate_event_report"
    started = time.perf_counter()
    plan = dict(state.get("query_plan") or {})
    severity_info = plan.get("severity_assessment") or {}
    diagnosis = plan.get("root_cause_diagnosis") or {}

    try:
        report = generate_event_report(dict(state.get("evidence_package") or {}))
        if severity_info.get("final_severity"):
            report["severity"] = severity_info["final_severity"]
        if diagnosis.get("root_cause"):
            report["root_cause"] = diagnosis["root_cause"]
        if diagnosis.get("action_suggestions"):
            report["action_suggestions"] = diagnosis["action_suggestions"]
        if diagnosis.get("evidence_refs"):
            report["evidence_refs"] = diagnosis["evidence_refs"]
        if diagnosis.get("affected_services"):
            report["affected_services"] = diagnosis["affected_services"]

        event = dict(state.get("trigger_event") or {})
        match_result = plan.get("rule_match") or {}
        report["trigger_event"] = {
            "log_id": event.get("log_id"),
            "trace_id": event.get("trace_id"),
            "service_name": event.get("service_name"),
            "error_code": event.get("error_code"),
            "timestamp": event.get("timestamp"),
        }
        report["rule_match"] = {
            "matched": match_result.get("matched"),
            "rule_id": match_result.get("rule_id"),
            "rule_name": match_result.get("rule_name"),
        }

        state["analysis_report"] = report
        degraded = bool(report.get("degraded"))
        append_node_trace(
            state,
            node,
            "success",
            duration_ms=_elapsed_ms(started),
            output_summary="降级事件报告" if degraded else "事件报告已生成",
        )
    except Exception as exc:  # noqa: BLE001
        record_error(state, node, str(exc))
        state["analysis_report"] = {
            "ok": False,
            "degraded": True,
            "report_type": "event",
            "title": "事件诊断报告生成失败",
            "severity": severity_info.get("final_severity") or "medium",
            "summary": str(exc),
            "root_cause": diagnosis.get("root_cause") or str(exc),
            "key_findings": [],
            "recommendations": ["请检查 LLM 与证据包配置"],
        }
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(state, "analysis_report", "node_trace", "errors")


def _derive_context_window(event: dict[str, Any]) -> dict[str, str]:
    """以触发事件时间为中心推导上下文查询窗口。"""
    anchor = _parse_iso_datetime(event.get("timestamp")) or datetime.now(timezone.utc)
    start = anchor - timedelta(minutes=_CONTEXT_WINDOW_BEFORE_MINUTES)
    end = anchor + timedelta(minutes=_CONTEXT_WINDOW_AFTER_MINUTES)
    return {"start": start.isoformat(), "end": end.isoformat()}


def _synthesize_severity(rule_severity: str, diagnosis: dict[str, Any]) -> str:
    """规则定级为主，高置信度 LLM 结论可上调严重等级。"""
    rule_rank = _SEVERITY_RANK.get(rule_severity.lower(), 1)
    llm_severity = _coerce_str(diagnosis.get("severity")) or "medium"
    llm_rank = _SEVERITY_RANK.get(llm_severity.lower(), 1)
    confidence = float(diagnosis.get("confidence") or 0.0)

    final_rank = rule_rank
    if confidence >= 0.7 and llm_rank > final_rank:
        final_rank = llm_rank
    elif confidence >= 0.85 and llm_rank < final_rank:
        final_rank = max(final_rank - 1, llm_rank)

    return _RANK_TO_SEVERITY.get(final_rank, "medium")


def _build_alert_title(
    event: dict[str, Any],
    diagnosis: dict[str, Any],
    match_result: dict[str, Any],
) -> str:
    service = _coerce_str(event.get("service_name"))
    error_code = _coerce_str(event.get("error_code"))
    rule_name = _coerce_str(match_result.get("rule_name"))

    if rule_name and service:
        return f"{rule_name}：{service}"
    if service and error_code:
        return f"{service} · {error_code} 异常"
    if diagnosis.get("root_cause"):
        return str(diagnosis["root_cause"])[:60]
    return "规则触发事件预警"


def _resolve_event_timestamp(event: dict[str, Any]) -> str:
    ts = event.get("timestamp")
    if isinstance(ts, str) and ts.strip():
        return ts.strip()
    if isinstance(ts, datetime):
        return ts.isoformat()
    return datetime.now(timezone.utc).isoformat()


def _normalize_trigger_log(event: dict[str, Any]) -> dict[str, Any]:
    return dict(event)


def _dedupe_logs(logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    picked: list[dict[str, Any]] = []
    for log in logs:
        key = _log_dedupe_key(log)
        if key in seen:
            continue
        seen.add(key)
        picked.append(log)
    return picked


def _log_dedupe_key(log: dict[str, Any]) -> str:
    for field in ("log_id", "id", "request_id", "trace_id"):
        value = log.get(field)
        if value is not None and str(value).strip():
            return f"{field}:{value}"
    timestamp = log.get("timestamp")
    service = log.get("service_name")
    message = str(log.get("message") or "")[:80]
    return f"fallback:{timestamp}:{service}:{message}"


def _parse_iso_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _coerce_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _elapsed_ms(started: float) -> int:
    return max(0, int((time.perf_counter() - started) * 1000))


def _pack(state: AnalysisState, *keys: str) -> dict[str, Any]:
    return {key: state[key] for key in keys if key in state}
