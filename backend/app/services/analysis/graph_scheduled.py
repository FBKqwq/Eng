"""定时任务子图。

职责：平台周期体检 + 业务洞察；聚合 → 证据 → 关系发现 → 报告。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.4

节点流：build_time_window -> plan_queries -> aggregate_metrics -> sample_logs
       -> build_evidence -> analyze_relations -> generate_report
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from langgraph.graph import END, StateGraph

from app.schemas.log import LogLevel, LogQueryRequest
from app.services.analysis.schemas import normalize_trigger
from app.services.analysis.state import (
    AnalysisState,
    append_node_trace,
    create_initial_state,
    record_error,
)
from app.services.elasticsearch import log_query_service
from app.services.langchain.evidence_builder import build_evidence_package
from app.services.langchain.relation_chain import discover_relations
from app.services.langchain.report_chain import generate_periodic_report
from app.services.tools.elasticsearch_tools import (
    EsAggregateMetricsInput,
    es_aggregate_metrics,
)

_AGGREGATE_TEMPLATES: tuple[str, ...] = (
    "traffic",
    "errors",
    "latency",
    "behavior_funnel",
    "security",
    "infra_health",
)

_NODE_ORDER: tuple[str, ...] = (
    "build_time_window",
    "plan_queries",
    "aggregate_metrics",
    "sample_logs",
    "build_evidence",
    "analyze_relations",
    "generate_report",
)


def build_scheduled_graph() -> Any:
    """构建并编译定时子图（LangGraph StateGraph）。"""
    return _compile_scheduled_graph()


def run_scheduled_subgraph(time_window: dict[str, Any] | None = None) -> dict[str, Any]:
    """执行定时子图；不负责持久化（由 scheduler 调 report_service 写入）。"""
    trigger_raw: dict[str, Any] = {
        "trigger_type": "scheduled",
        "time_window": time_window or {},
    }
    normalized = normalize_trigger(trigger_raw)
    if not normalized.get("ok"):
        error_msg = str(normalized.get("error") or "invalid trigger")
        return {
            "ok": False,
            "report": {},
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
    state = create_initial_state(
        "scheduled",
        time_window=trigger.get("time_window") or {},
        trigger_event=trigger.get("trigger_event") or {},
    )
    # create_initial_state 复用模块级空容器，需重置以免多次运行污染各列表/字典字段
    state["node_trace"] = []
    state["errors"] = []
    state["raw_logs"] = []
    state["metrics"] = {}
    state["query_plan"] = {}
    state["evidence_package"] = {}
    state["relations"] = []
    state["analysis_report"] = {}

    graph = build_scheduled_graph()
    final_state: AnalysisState = graph.invoke(state)

    report = final_state.get("analysis_report") or {}
    return {
        "ok": bool(report),
        "report": report,
        "node_trace": list(final_state.get("node_trace") or []),
        "errors": list(final_state.get("errors") or []),
    }


@lru_cache(maxsize=1)
def _compile_scheduled_graph() -> Any:
    graph = StateGraph(AnalysisState)
    graph.add_node("build_time_window", _node_build_time_window)
    graph.add_node("plan_queries", _node_plan_queries)
    graph.add_node("aggregate_metrics", _node_aggregate_metrics)
    graph.add_node("sample_logs", _node_sample_logs)
    graph.add_node("build_evidence", _node_build_evidence)
    graph.add_node("analyze_relations", _node_analyze_relations)
    graph.add_node("generate_report", _node_generate_report)

    graph.set_entry_point("build_time_window")
    for current, nxt in zip(_NODE_ORDER, _NODE_ORDER[1:], strict=False):
        graph.add_edge(current, nxt)
    graph.add_edge("generate_report", END)
    return graph.compile()


def _node_build_time_window(state: AnalysisState) -> dict[str, Any]:
    node = "build_time_window"
    started = time.perf_counter()
    try:
        window = dict(state.get("time_window") or {})
        start_dt = _parse_iso_datetime(window.get("start"))
        end_dt = _parse_iso_datetime(window.get("end"))
        if start_dt is None or end_dt is None:
            raise ValueError("时间窗口 start/end 缺失或无法解析")
        if end_dt <= start_dt:
            raise ValueError("时间窗口 end 必须大于 start")

        enriched = {
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "duration_seconds": int((end_dt - start_dt).total_seconds()),
        }
        state["time_window"] = enriched
        append_node_trace(
            state,
            node,
            "success",
            duration_ms=_elapsed_ms(started),
            output_summary=f"窗口 {enriched['duration_seconds']}s",
        )
    except Exception as exc:  # noqa: BLE001 - 节点级降级，不中断整图
        record_error(state, node, str(exc))
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(state, "time_window", "node_trace", "errors")


def _node_plan_queries(state: AnalysisState) -> dict[str, Any]:
    node = "plan_queries"
    started = time.perf_counter()
    try:
        state["query_plan"] = {
            "aggregate_templates": list(_AGGREGATE_TEMPLATES),
            "sample_logs": {
                "error_limit": 30,
                "general_limit": 20,
                "max_total": 50,
            },
            "planner": "rule_v1",
        }
        append_node_trace(
            state,
            node,
            "success",
            duration_ms=_elapsed_ms(started),
            output_summary=f"{len(_AGGREGATE_TEMPLATES)} 个聚合模板",
        )
    except Exception as exc:  # noqa: BLE001
        record_error(state, node, str(exc))
        state.setdefault("query_plan", {})
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(state, "query_plan", "node_trace", "errors")


def _node_aggregate_metrics(state: AnalysisState) -> dict[str, Any]:
    node = "aggregate_metrics"
    started = time.perf_counter()
    metrics: dict[str, Any] = dict(state.get("metrics") or {})
    failed_templates: list[str] = []

    try:
        start_dt, end_dt = _require_window_datetimes(state, node)
        templates = (
            state.get("query_plan") or {}
        ).get("aggregate_templates") or list(_AGGREGATE_TEMPLATES)

        for template in templates:
            result = es_aggregate_metrics(
                EsAggregateMetricsInput(
                    template=template,  # type: ignore[arg-type]
                    start_time=start_dt,
                    end_time=end_dt,
                )
            )
            metrics[template] = result
            if not result.get("ok"):
                failed_templates.append(template)
                record_error(
                    state,
                    node,
                    f"{template}: {result.get('error') or '聚合不可用'}",
                )

        state["metrics"] = metrics
        success_count = len(templates) - len(failed_templates)
        append_node_trace(
            state,
            node,
            "success",
            duration_ms=_elapsed_ms(started),
            output_summary=f"{success_count}/{len(templates)} 模板成功",
        )
    except Exception as exc:  # noqa: BLE001
        record_error(state, node, str(exc))
        state["metrics"] = metrics
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(state, "metrics", "node_trace", "errors")


def _node_sample_logs(state: AnalysisState) -> dict[str, Any]:
    node = "sample_logs"
    started = time.perf_counter()
    items: list[dict[str, Any]] = []

    try:
        start_dt, end_dt = _require_window_datetimes(state, node)
        sample_plan = (state.get("query_plan") or {}).get("sample_logs") or {}
        error_limit = int(sample_plan.get("error_limit") or 30)
        general_limit = int(sample_plan.get("general_limit") or 20)
        max_total = int(sample_plan.get("max_total") or 50)

        seen_keys: set[str] = set()

        error_request = LogQueryRequest(
            start_time=start_dt,
            end_time=end_dt,
            log_levels=[LogLevel.error, LogLevel.critical],
            page=1,
            page_size=error_limit,
        )
        error_result = log_query_service.search_logs(error_request)
        if error_result.get("available"):
            items.extend(
                _dedupe_logs(error_result.get("items") or [], seen_keys, max_total)
            )
        else:
            record_error(
                state,
                node,
                f"ERROR 样本查询失败: {error_result.get('error') or 'ES 不可用'}",
            )

        if len(items) < max_total:
            general_request = LogQueryRequest(
                start_time=start_dt,
                end_time=end_dt,
                page=1,
                page_size=general_limit,
            )
            general_result = log_query_service.search_logs(general_request)
            if general_result.get("available"):
                items.extend(
                    _dedupe_logs(general_result.get("items") or [], seen_keys, max_total)
                )
            else:
                record_error(
                    state,
                    node,
                    f"通用样本查询失败: {general_result.get('error') or 'ES 不可用'}",
                )

        state["raw_logs"] = items[:max_total]
        append_node_trace(
            state,
            node,
            "success",
            duration_ms=_elapsed_ms(started),
            output_summary=f"采样 {len(state['raw_logs'])} 条",
        )
    except Exception as exc:  # noqa: BLE001
        record_error(state, node, str(exc))
        state["raw_logs"] = items
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(state, "raw_logs", "node_trace", "errors")


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


def _node_analyze_relations(state: AnalysisState) -> dict[str, Any]:
    node = "analyze_relations"
    started = time.perf_counter()
    try:
        package = dict(state.get("evidence_package") or {})
        result = discover_relations(package)
        relations = list(result.get("relations") or [])
        state["relations"] = relations

        degraded = bool(result.get("degraded"))
        if degraded or not relations:
            summary = (
                "关系发现降级，空关系列表"
                if degraded
                else "未发现隐藏关系"
            )
            append_node_trace(
                state,
                node,
                "skipped",
                duration_ms=_elapsed_ms(started),
                output_summary=summary,
            )
        else:
            append_node_trace(
                state,
                node,
                "success",
                duration_ms=_elapsed_ms(started),
                output_summary=f"发现 {len(relations)} 条关系",
            )
    except Exception as exc:  # noqa: BLE001
        record_error(state, node, str(exc))
        state["relations"] = []
        append_node_trace(
            state,
            node,
            "failed",
            duration_ms=_elapsed_ms(started),
            error_message=str(exc),
        )
    return _pack(state, "relations", "node_trace", "errors")


def _node_generate_report(state: AnalysisState) -> dict[str, Any]:
    node = "generate_report"
    started = time.perf_counter()
    try:
        evidence = dict(state.get("evidence_package") or {})
        relations = list(state.get("relations") or [])
        report_input = (
            {**evidence, "relations": relations} if relations else evidence
        )
        report = generate_periodic_report(report_input)
        if relations:
            report = dict(report)
            report["relations"] = relations
        state["analysis_report"] = report
        degraded = bool(report.get("degraded"))
        append_node_trace(
            state,
            node,
            "success",
            duration_ms=_elapsed_ms(started),
            output_summary="降级模板报告" if degraded else "周期报告已生成",
        )
    except Exception as exc:  # noqa: BLE001
        record_error(state, node, str(exc))
        state["analysis_report"] = {
            "ok": False,
            "degraded": True,
            "report_type": "periodic",
            "title": "周期报告生成失败",
            "risk_level": "medium",
            "summary": str(exc),
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


def _require_window_datetimes(
    state: AnalysisState,
    node_name: str,
) -> tuple[datetime, datetime]:
    window = state.get("time_window") or {}
    start_dt = _parse_iso_datetime(window.get("start"))
    end_dt = _parse_iso_datetime(window.get("end"))
    if start_dt is None or end_dt is None:
        raise ValueError(f"{node_name}: 时间窗口不可用，请先执行 build_time_window")
    return start_dt, end_dt


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


def _dedupe_logs(
    logs: list[dict[str, Any]],
    seen_keys: set[str],
    max_total: int,
) -> list[dict[str, Any]]:
    picked: list[dict[str, Any]] = []
    for log in logs:
        if len(seen_keys) >= max_total:
            break
        key = _log_dedupe_key(log)
        if key in seen_keys:
            continue
        seen_keys.add(key)
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


def _elapsed_ms(started: float) -> int:
    return max(0, int((time.perf_counter() - started) * 1000))


def _pack(state: AnalysisState, *keys: str) -> dict[str, Any]:
    return {key: state[key] for key in keys if key in state}
