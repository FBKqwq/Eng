"""LangGraph 主图。

职责：路由调度、结果收敛、预警决策、持久化；不做具体分析。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.3

节点流：normalize_trigger -> build_state -> route -> [scheduled|rule 子图]
       -> merge_result -> alert_decision -> persist_result -> END
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from langgraph.graph import END, StateGraph

from app.services.alert.alert_service import write_alert
from app.services.alert.dedup import check_duplicate
from app.services.analysis.graph_rule import run_rule_subgraph
from app.services.analysis.graph_scheduled import run_scheduled_subgraph
from app.services.analysis.schemas import normalize_trigger
from app.services.analysis.state import (
    AnalysisState,
    append_node_trace,
    create_initial_state,
    record_error,
)
from app.services.langchain.alert_chain import explain_alert
from app.services.report.report_service import write_report

_SEVERITY_RANK: dict[str, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


def build_main_graph() -> Any:
    """构建并编译主图（LangGraph StateGraph，子图作为节点挂载）。"""
    return _compile_main_graph()


def run_main_graph(trigger_type: str, **kwargs: Any) -> dict[str, Any]:
    """手动触发主图执行；持久化仅在 persist_result 节点收口。"""
    raw_trigger: dict[str, Any] = {"trigger_type": trigger_type, **kwargs}
    state = create_initial_state(trigger_type, **kwargs)
    _reset_mutable_state(state)
    state["query_plan"] = {"raw_trigger": raw_trigger}

    graph = build_main_graph()
    final_state: AnalysisState = graph.invoke(state)
    persist = final_state.get("persist_result") or {}
    report_id = persist.get("report_id")
    report_write_ok = bool(persist.get("report_write_ok"))

    return {
        "ok": report_write_ok and bool(report_id),
        "report_id": report_id,
        "alert_id": persist.get("alert_id"),
        "node_trace": list(final_state.get("node_trace") or []),
        "alert_decision": dict(final_state.get("alert_decision") or {}),
        "errors": list(final_state.get("errors") or []),
    }


@lru_cache(maxsize=1)
def _compile_main_graph() -> Any:
    graph = StateGraph(AnalysisState)
    graph.add_node("normalize_trigger", _node_normalize_trigger)
    graph.add_node("build_state", _node_build_state)
    graph.add_node("run_scheduled_subgraph", _node_run_scheduled_subgraph)
    graph.add_node("run_rule_subgraph", _node_run_rule_subgraph)
    graph.add_node("merge_result", _node_merge_result)
    graph.add_node("main_alert_decision", _node_alert_decision)
    graph.add_node("main_persist_result", _node_persist_result)

    graph.set_entry_point("normalize_trigger")
    graph.add_edge("normalize_trigger", "build_state")
    graph.add_conditional_edges(
        "build_state",
        _route_by_trigger_type,
        {
            "scheduled": "run_scheduled_subgraph",
            "rule": "run_rule_subgraph",
            "invalid": "merge_result",
        },
    )
    graph.add_edge("run_scheduled_subgraph", "merge_result")
    graph.add_edge("run_rule_subgraph", "merge_result")
    graph.add_edge("merge_result", "main_alert_decision")
    graph.add_edge("main_alert_decision", "main_persist_result")
    graph.add_edge("main_persist_result", END)
    return graph.compile()


def _node_normalize_trigger(state: AnalysisState) -> dict[str, Any]:
    node = "normalize_trigger"
    started = time.perf_counter()
    plan = dict(state.get("query_plan") or {})
    raw = plan.get("raw_trigger")
    if not isinstance(raw, dict):
        raw = {
            "trigger_type": state.get("trigger_type"),
            "trigger_event": state.get("trigger_event") or {},
            "time_window": state.get("time_window") or {},
        }

    try:
        result = normalize_trigger(raw)
        if not result.get("ok"):
            raise ValueError(str(result.get("error") or "invalid trigger"))

        trigger = dict(result["trigger"])
        state["trigger_type"] = trigger.get("trigger_type") or state.get("trigger_type")
        state["trigger_event"] = dict(trigger.get("trigger_event") or {})
        state["time_window"] = dict(trigger.get("time_window") or {})
        plan["normalized_trigger"] = trigger
        plan["trigger_valid"] = True
        state["query_plan"] = plan

        append_node_trace(
            state,
            node,
            "success",
            duration_ms=_elapsed_ms(started),
            output_summary=f"触发类型 {state.get('trigger_type')}",
        )
    except Exception as exc:  # noqa: BLE001 - 节点级降级，不中断整图
        record_error(state, node, str(exc))
        plan["trigger_valid"] = False
        state["query_plan"] = plan
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(state, "trigger_type", "trigger_event", "time_window", "query_plan", "node_trace", "errors")


def _node_build_state(state: AnalysisState) -> dict[str, Any]:
    node = "build_state"
    started = time.perf_counter()

    try:
        if not state.get("task_id"):
            state["task_id"] = create_initial_state(
                state.get("trigger_type") or "scheduled"
            ).get("task_id")

        for key in (
            "raw_logs",
            "metrics",
            "relations",
            "evidence_package",
            "analysis_report",
            "alert_candidate",
            "alert_decision",
            "persist_result",
        ):
            if key == "raw_logs" or key == "relations":
                state[key] = []
            elif key in ("metrics", "evidence_package", "analysis_report", "alert_candidate", "alert_decision", "persist_result"):
                state[key] = {}

        append_node_trace(
            state,
            node,
            "success",
            duration_ms=_elapsed_ms(started),
            output_summary=f"task_id={state.get('task_id')}",
        )
    except Exception as exc:  # noqa: BLE001
        record_error(state, node, str(exc))
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(
        state,
        "task_id",
        "raw_logs",
        "metrics",
        "relations",
        "evidence_package",
        "analysis_report",
        "alert_candidate",
        "alert_decision",
        "persist_result",
        "node_trace",
        "errors",
    )


def _node_run_scheduled_subgraph(state: AnalysisState) -> dict[str, Any]:
    node = "run_scheduled_subgraph"
    started = time.perf_counter()

    try:
        result = run_scheduled_subgraph(time_window=dict(state.get("time_window") or {}))
        plan = dict(state.get("query_plan") or {})
        plan["subgraph_result"] = result
        state["query_plan"] = plan
        state["analysis_report"] = dict(result.get("report") or {})
        _merge_subgraph_errors(state, result)

        summary = "子图成功" if result.get("ok") else "子图降级"
        append_node_trace(
            state,
            node,
            "success" if result.get("ok") else "failed",
            duration_ms=_elapsed_ms(started),
            output_summary=summary,
            error_message=None if result.get("ok") else "子图未产出有效报告",
        )
    except Exception as exc:  # noqa: BLE001
        record_error(state, node, str(exc))
        plan = dict(state.get("query_plan") or {})
        plan["subgraph_result"] = {"ok": False, "report": {}, "node_trace": [], "errors": []}
        state["query_plan"] = plan
        state["analysis_report"] = {}
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(state, "query_plan", "analysis_report", "node_trace", "errors")


def _node_run_rule_subgraph(state: AnalysisState) -> dict[str, Any]:
    node = "run_rule_subgraph"
    started = time.perf_counter()

    try:
        result = run_rule_subgraph(trigger_event=dict(state.get("trigger_event") or {}))
        plan = dict(state.get("query_plan") or {})
        plan["subgraph_result"] = result
        state["query_plan"] = plan
        state["analysis_report"] = dict(result.get("report") or {})
        state["alert_candidate"] = dict(result.get("alert_candidate") or {})
        _merge_subgraph_errors(state, result)

        summary = "子图成功" if result.get("ok") else "子图降级"
        append_node_trace(
            state,
            node,
            "success" if result.get("ok") else "failed",
            duration_ms=_elapsed_ms(started),
            output_summary=summary,
            error_message=None if result.get("ok") else "子图未产出有效报告",
        )
    except Exception as exc:  # noqa: BLE001
        record_error(state, node, str(exc))
        plan = dict(state.get("query_plan") or {})
        plan["subgraph_result"] = {
            "ok": False,
            "report": {},
            "alert_candidate": {},
            "node_trace": [],
            "errors": [],
        }
        state["query_plan"] = plan
        state["analysis_report"] = {}
        state["alert_candidate"] = {}
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(state, "query_plan", "analysis_report", "alert_candidate", "node_trace", "errors")


def _node_merge_result(state: AnalysisState) -> dict[str, Any]:
    node = "merge_result"
    started = time.perf_counter()

    try:
        plan = dict(state.get("query_plan") or {})
        subgraph_result = plan.get("subgraph_result") or {}
        raw_report = dict(state.get("analysis_report") or subgraph_result.get("report") or {})

        if not raw_report:
            raw_report = _build_fallback_report(state)

        normalized = _normalize_report(state, raw_report)
        state["analysis_report"] = normalized

        trigger_type = (state.get("trigger_type") or "").lower()
        prefix = f"{trigger_type}." if trigger_type else "subgraph."
        for entry in subgraph_result.get("node_trace") or []:
            if not isinstance(entry, dict):
                continue
            merged = dict(entry)
            sub_node = str(entry.get("node_name") or "unknown")
            merged["node_name"] = f"{prefix}{sub_node}"
            state.setdefault("node_trace", []).append(merged)

        append_node_trace(
            state,
            node,
            "success",
            duration_ms=_elapsed_ms(started),
            output_summary=f"报告类型 {normalized.get('report_type')}",
        )
    except Exception as exc:  # noqa: BLE001
        record_error(state, node, str(exc))
        state["analysis_report"] = _build_fallback_report(state, error=str(exc))
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(state, "analysis_report", "node_trace", "errors")


def _node_alert_decision(state: AnalysisState) -> dict[str, Any]:
    node = "alert_decision"
    started = time.perf_counter()

    decision: dict[str, Any] = {
        "should_alert": False,
        "is_duplicate": False,
        "existing_alert_id": None,
        "idempotency_key": None,
        "explanation": None,
        "alert_candidate": {},
    }

    try:
        trigger_type = (state.get("trigger_type") or "").lower()
        report = dict(state.get("analysis_report") or {})
        alert_candidate: dict[str, Any] = {}

        if trigger_type == "rule":
            alert_candidate = dict(state.get("alert_candidate") or {})
            severity = _coerce_str(
                alert_candidate.get("severity") or report.get("severity")
            ).lower() or "medium"
            decision["should_alert"] = _severity_at_least_high(severity)
        elif trigger_type == "scheduled":
            risk_level = _coerce_str(report.get("risk_level")).lower() or "medium"
            decision["should_alert"] = risk_level == "high"
            if decision["should_alert"]:
                alert_candidate = _build_scheduled_alert_candidate(state, report)
        else:
            record_error(state, node, f"未知触发类型 {trigger_type!r}，跳过预警决策")

        decision["alert_candidate"] = alert_candidate

        if decision["should_alert"] and alert_candidate:
            dedup_result = check_duplicate(alert_candidate)
            decision["is_duplicate"] = bool(dedup_result.get("is_duplicate"))
            decision["existing_alert_id"] = dedup_result.get("existing_alert_id")
            decision["idempotency_key"] = dedup_result.get("idempotency_key")
            if not dedup_result.get("ok"):
                record_error(
                    state,
                    node,
                    str(dedup_result.get("error") or "去重检查失败"),
                )

            explanation = explain_alert(alert_candidate)
            decision["explanation"] = explanation
            if explanation.get("title"):
                alert_candidate["title"] = explanation["title"]
            if explanation.get("detail"):
                alert_candidate["description"] = explanation["detail"]
            decision["alert_candidate"] = alert_candidate

        state["alert_decision"] = decision
        state["alert_candidate"] = alert_candidate

        alert_summary = "出预警" if decision["should_alert"] else "无需预警"
        if decision["should_alert"] and decision["is_duplicate"]:
            alert_summary = "预警去重命中"
        append_node_trace(
            state,
            node,
            "success",
            duration_ms=_elapsed_ms(started),
            output_summary=alert_summary,
        )
    except Exception as exc:  # noqa: BLE001
        record_error(state, node, str(exc))
        decision["error"] = str(exc)
        state["alert_decision"] = decision
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(state, "alert_decision", "alert_candidate", "node_trace", "errors")


def _node_persist_result(state: AnalysisState) -> dict[str, Any]:
    node = "persist_result"
    started = time.perf_counter()
    persist: dict[str, Any] = {
        "report_id": None,
        "alert_id": None,
        "report_write_ok": False,
        "alert_write_ok": False,
    }

    try:
        report_for_write = _prepare_report_for_persist(state)
        write_report_result = write_report(report_for_write)
        persist["report_write_ok"] = bool(write_report_result.get("ok"))
        persist["report_id"] = write_report_result.get("report_id")
        if not write_report_result.get("ok"):
            record_error(
                state,
                node,
                str(write_report_result.get("error") or "报告写入失败"),
            )

        decision = dict(state.get("alert_decision") or {})
        if decision.get("should_alert"):
            candidate = dict(decision.get("alert_candidate") or {})
            if decision.get("is_duplicate") and decision.get("existing_alert_id"):
                candidate["existing_alert_id"] = decision["existing_alert_id"]
                alert_write = write_alert(candidate)
                persist["alert_write_ok"] = bool(alert_write.get("ok"))
                persist["alert_id"] = decision["existing_alert_id"]
                if not alert_write.get("ok"):
                    record_error(
                        state,
                        node,
                        str(alert_write.get("error") or "预警累加失败"),
                    )
            elif not decision.get("is_duplicate"):
                alert_write = write_alert(candidate)
                persist["alert_write_ok"] = bool(alert_write.get("ok"))
                persist["alert_id"] = alert_write.get("alert_id")
                if not alert_write.get("ok"):
                    record_error(
                        state,
                        node,
                        str(alert_write.get("error") or "预警写入失败"),
                    )

        state["persist_result"] = persist
        summary_parts = []
        if persist.get("report_id"):
            summary_parts.append(f"report={persist['report_id'][:8]}")
        if persist.get("alert_id"):
            summary_parts.append(f"alert={str(persist['alert_id'])[:8]}")
        append_node_trace(
            state,
            node,
            "success",
            duration_ms=_elapsed_ms(started),
            output_summary="；".join(summary_parts) if summary_parts else "持久化完成",
        )
    except Exception as exc:  # noqa: BLE001
        record_error(state, node, str(exc))
        state["persist_result"] = persist
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(state, "persist_result", "node_trace", "errors")


def _route_by_trigger_type(state: AnalysisState) -> str:
    plan = state.get("query_plan") or {}
    if not plan.get("trigger_valid", True):
        return "invalid"

    trigger_type = _coerce_str(state.get("trigger_type")).lower()
    if trigger_type == "scheduled":
        return "scheduled"
    if trigger_type == "rule":
        return "rule"
    return "invalid"


def _normalize_report(state: AnalysisState, report: dict[str, Any]) -> dict[str, Any]:
    trigger_type = _coerce_str(state.get("trigger_type")).lower() or "unknown"
    default_type = "periodic" if trigger_type == "scheduled" else "event"

    normalized: dict[str, Any] = {
        "task_id": state.get("task_id"),
        "trigger_type": trigger_type,
        "report_type": report.get("report_type") or default_type,
        "title": report.get("title") or "",
        "summary": report.get("summary") or "",
        "risk_level": report.get("risk_level") or report.get("severity") or "medium",
        "degraded": bool(report.get("degraded")),
        "key_findings": list(report.get("key_findings") or []),
        "recommendations": list(report.get("recommendations") or []),
    }

    if report.get("severity") is not None:
        normalized["severity"] = report.get("severity")
    if report.get("root_cause") is not None:
        normalized["root_cause"] = report.get("root_cause")
    if report.get("trigger_event") is not None:
        normalized["trigger_event"] = report.get("trigger_event")
    if report.get("rule_match") is not None:
        normalized["rule_match"] = report.get("rule_match")
    if report.get("action_suggestions") is not None:
        normalized["action_suggestions"] = report.get("action_suggestions")
    if report.get("evidence_refs") is not None:
        normalized["evidence_refs"] = report.get("evidence_refs")
    if report.get("affected_services") is not None:
        normalized["affected_services"] = report.get("affected_services")
    if report.get("ok") is not None:
        normalized["ok"] = report.get("ok")

    return normalized


def _build_fallback_report(
    state: AnalysisState,
    *,
    error: str | None = None,
) -> dict[str, Any]:
    trigger_type = _coerce_str(state.get("trigger_type")).lower() or "unknown"
    report_type = "periodic" if trigger_type == "scheduled" else "event"
    return {
        "ok": False,
        "degraded": True,
        "report_type": report_type,
        "title": "分析报告生成失败",
        "summary": error or "子图未产出有效报告",
        "risk_level": "medium",
        "key_findings": [],
        "recommendations": ["请检查子图执行日志与基础设施连通性"],
    }


def _build_scheduled_alert_candidate(
    state: AnalysisState,
    report: dict[str, Any],
) -> dict[str, Any]:
    findings = report.get("key_findings") or []
    affected = "platform"
    if isinstance(findings, list) and findings:
        first = findings[0]
        if isinstance(first, dict) and first.get("service"):
            affected = str(first["service"])

    return {
        "alert_type": "periodic_risk_high",
        "severity": "high",
        "title": report.get("title") or "周期体检高风险预警",
        "affected_service": affected,
        "description": report.get("summary") or "周期分析检测到高风险",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "task_id": state.get("task_id"),
            "risk_level": report.get("risk_level"),
            "key_findings": findings[:5],
        },
    }


def _prepare_report_for_persist(state: AnalysisState) -> dict[str, Any]:
    report = dict(state.get("analysis_report") or {})
    report["node_trace"] = list(state.get("node_trace") or [])
    report["task_id"] = state.get("task_id")
    report["trigger_type"] = state.get("trigger_type")
    decision = state.get("alert_decision") or {}
    if decision:
        report["alert_decision"] = dict(decision)
    return report


def _merge_subgraph_errors(state: AnalysisState, subgraph_result: dict[str, Any]) -> None:
    for err in subgraph_result.get("errors") or []:
        if not isinstance(err, dict):
            continue
        errors = state.setdefault("errors", [])
        if err not in errors:
            errors.append(err)


def _reset_mutable_state(state: AnalysisState) -> None:
    state["node_trace"] = []
    state["errors"] = []
    state["raw_logs"] = []
    state["metrics"] = {}
    state["query_plan"] = {}
    state["evidence_package"] = {}
    state["relations"] = []
    state["analysis_report"] = {}
    state["alert_candidate"] = {}
    state["alert_decision"] = {}
    state["persist_result"] = {}


def _severity_at_least_high(severity: str) -> bool:
    return _SEVERITY_RANK.get(severity.lower(), 1) >= _SEVERITY_RANK["high"]


def _coerce_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _elapsed_ms(started: float) -> int:
    return max(0, int((time.perf_counter() - started) * 1000))


def _pack(state: AnalysisState, *keys: str) -> dict[str, Any]:
    return {key: state[key] for key in keys if key in state}
