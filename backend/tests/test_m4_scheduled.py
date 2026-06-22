"""M4-08：定时闭环单元测试（全程 mock ES/LLM/子图依赖，不联网）。"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.analysis.graph_scheduled import run_scheduled_subgraph
from app.services.analysis.scheduler import run_once
from app.services.analysis.schemas import normalize_trigger
from app.services.analysis.state import (
    append_node_trace,
    create_initial_state,
    record_error,
)
from app.services.report import report_service

_PATCH_ES = "app.services.report.report_service.get_es_client"

_TIME_WINDOW = {
    "start": "2026-06-22T10:00:00",
    "end": "2026-06-22T11:00:00",
}

_PERIODIC_REPORT: dict[str, Any] = {
    "ok": True,
    "degraded": False,
    "report_type": "periodic",
    "title": "测试周期报告",
    "risk_level": "low",
    "summary": "系统运行平稳",
    "key_findings": ["错误率正常"],
    "recommendations": ["持续观察"],
}

_SAMPLE_LOG = {
    "log_id": "log-001",
    "log_level": "ERROR",
    "service_name": "order-service",
    "message": "订单超时",
    "timestamp": "2026-06-22T10:30:00",
}


def _assert_no_placeholder(obj: Any) -> None:
    """递归检查产出 dict 不含 placeholder 键。"""
    if isinstance(obj, dict):
        assert "placeholder" not in obj
        for value in obj.values():
            _assert_no_placeholder(value)
    elif isinstance(obj, list):
        for item in obj:
            _assert_no_placeholder(item)


def _make_es_client_for_write() -> MagicMock:
    client = MagicMock()
    options_client = MagicMock()
    client.options.return_value = options_client
    options_client.index.return_value = {"result": "created"}
    return client


def _make_es_client_for_list(*, items: list[dict[str, Any]] | None = None) -> MagicMock:
    hits = [
        {
            "_id": item.get("report_id", f"id-{idx}"),
            "_source": item,
        }
        for idx, item in enumerate(items or [])
    ]
    client = MagicMock()
    options_client = MagicMock()
    client.options.return_value = options_client
    options_client.search.return_value = {
        "hits": {
            "total": {"value": len(hits)},
            "hits": hits,
        }
    }
    return client


def _mock_aggregate_ok(params: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "tool": "es_aggregate_metrics",
        "template": params.template,
        "buckets": [{"key": "order-service", "count": 3}],
    }


def _mock_search_ok(request: Any) -> dict[str, Any]:
    return {
        "available": True,
        "error": None,
        "items": [_SAMPLE_LOG],
        "total": 1,
        "page": request.page,
        "page_size": request.page_size,
        "has_more": False,
        "took_ms": 5,
    }


def _mock_evidence(logs: list[dict[str, Any]], metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "evidence_package": {
            "summary": {"total_logs": len(logs), "error_count": 1, "warn_count": 0},
            "grouped": {"by_service": {"order-service": 1}},
            "samples": logs[:1],
            "metrics": metrics,
        },
        "input_log_count": len(logs),
        "sampled_count": min(len(logs), 1),
    }


def _install_subgraph_mocks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.analysis.graph_scheduled.es_aggregate_metrics",
        _mock_aggregate_ok,
    )
    monkeypatch.setattr(
        "app.services.analysis.graph_scheduled.log_query_service.search_logs",
        _mock_search_ok,
    )
    monkeypatch.setattr(
        "app.services.analysis.graph_scheduled.build_evidence_package",
        _mock_evidence,
    )
    monkeypatch.setattr(
        "app.services.analysis.graph_scheduled.generate_periodic_report",
        lambda pkg: dict(_PERIODIC_REPORT),
    )


# ---------------------------------------------------------------------------
# report_service（mock ES）
# ---------------------------------------------------------------------------


def test_write_report_success(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_es_client_for_write()
    monkeypatch.setattr(_PATCH_ES, lambda: client)

    result = report_service.write_report(
        {"report_type": "periodic", "title": "写入测试", "summary": "摘要"}
    )

    assert result["ok"] is True
    assert "report_id" in result
    assert result["report_id"]
    options_client = client.options.return_value
    options_client.index.assert_called_once()
    call_kwargs = options_client.index.call_args.kwargs
    assert call_kwargs["document"]["report_type"] == "periodic"
    assert call_kwargs["document"]["report_id"] == result["report_id"]
    assert call_kwargs["index"].startswith("analysis-results-")
    _assert_no_placeholder(result)


def test_write_report_es_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MagicMock()
    options_client = MagicMock()
    client.options.return_value = options_client
    options_client.index.side_effect = RuntimeError("ES 连接失败")
    monkeypatch.setattr(_PATCH_ES, lambda: client)

    result = report_service.write_report({"report_type": "periodic", "title": "失败测试"})

    assert result["ok"] is False
    assert "error" in result
    assert "ES 连接失败" in result["error"]
    _assert_no_placeholder(result)


def test_list_recent_reports_success(monkeypatch: pytest.MonkeyPatch) -> None:
    items = [
        {
            "report_id": "rpt-001",
            "report_type": "periodic",
            "title": "最近报告",
            "risk_level": "low",
            "summary": "摘要",
            "created_at": "2026-06-22T12:00:00Z",
            "task_id": "task-1",
        }
    ]
    monkeypatch.setattr(_PATCH_ES, lambda: _make_es_client_for_list(items=items))

    result = report_service.list_recent_reports(limit=10, report_type="periodic")

    assert result["ok"] is True
    assert result["total"] == 1
    assert result["limit"] == 10
    assert len(result["items"]) == 1
    assert result["items"][0]["report_id"] == "rpt-001"
    assert result["items"][0]["title"] == "最近报告"
    _assert_no_placeholder(result)


def test_get_report_found(monkeypatch: pytest.MonkeyPatch) -> None:
    doc = {
        "report_id": "rpt-abc",
        "report_type": "periodic",
        "title": "单份报告",
        "summary": "详情",
        "created_at": "2026-06-22T12:00:00Z",
    }
    monkeypatch.setattr(_PATCH_ES, lambda: _make_es_client_for_list(items=[doc]))

    result = report_service.get_report("rpt-abc")

    assert result["ok"] is True
    assert result["report_id"] == "rpt-abc"
    assert result["report"] is not None
    assert result["report"]["title"] == "单份报告"
    _assert_no_placeholder(result)


def test_get_report_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_PATCH_ES, lambda: _make_es_client_for_list(items=[]))

    result = report_service.get_report("missing-id")

    assert result["ok"] is True
    assert result["report_id"] == "missing-id"
    assert result["report"] is None
    _assert_no_placeholder(result)


# ---------------------------------------------------------------------------
# normalize_trigger
# ---------------------------------------------------------------------------


def test_normalize_trigger_scheduled() -> None:
    result = normalize_trigger(
        {
            "trigger_type": "scheduled",
            "task_name": "periodic_health",
            "time_window": dict(_TIME_WINDOW),
        }
    )

    assert result["ok"] is True
    trigger = result["trigger"]
    assert trigger["trigger_type"] == "scheduled"
    assert trigger["source"] == "scheduler"
    assert trigger["time_window"]["start"]
    assert trigger["time_window"]["end"]
    _assert_no_placeholder(result)


def test_normalize_trigger_rule() -> None:
    result = normalize_trigger(
        {
            "trigger_type": "rule",
            "trigger_event": {"trigger_rule": "high_error_rate"},
            "time_window": dict(_TIME_WINDOW),
            "source": "custom_scanner",
        }
    )

    assert result["ok"] is True
    trigger = result["trigger"]
    assert trigger["trigger_type"] == "rule"
    assert trigger["source"] == "custom_scanner"
    assert trigger["trigger_event"]["trigger_rule"] == "high_error_rate"
    _assert_no_placeholder(result)


@pytest.mark.parametrize(
    "raw",
    [
        {"trigger_type": "manual"},
        {"trigger_type": ""},
        "not-a-dict",
    ],
)
def test_normalize_trigger_invalid_type(raw: Any) -> None:
    result = normalize_trigger(raw)

    assert result["ok"] is False
    assert result["error"] == "invalid trigger_type"
    _assert_no_placeholder(result)


# ---------------------------------------------------------------------------
# state 辅助
# ---------------------------------------------------------------------------


def test_create_initial_state() -> None:
    state = create_initial_state(
        "scheduled",
        time_window=dict(_TIME_WINDOW),
        trigger_event={"task_name": "health"},
        task_id="fixed-task-id",
    )

    assert state["trigger_type"] == "scheduled"
    assert state["task_id"] == "fixed-task-id"
    assert state["time_window"] == _TIME_WINDOW
    assert state["node_trace"] == []
    assert state["errors"] == []
    _assert_no_placeholder(dict(state))


def test_append_node_trace() -> None:
    state = create_initial_state("scheduled")

    append_node_trace(
        state,
        "aggregate_metrics",
        "success",
        duration_ms=120,
        output_summary="6/6 模板成功",
    )

    assert len(state["node_trace"]) == 1
    entry = state["node_trace"][0]
    assert entry["node_name"] == "aggregate_metrics"
    assert entry["status"] == "success"
    assert entry["duration_ms"] == 120
    assert entry["output_summary"] == "6/6 模板成功"
    assert entry["started_at"] is not None
    assert entry["ended_at"] is not None
    _assert_no_placeholder(entry)


def test_record_error() -> None:
    state = create_initial_state("scheduled")

    record_error(state, "sample_logs", "ES 样本查询失败")

    assert len(state["errors"]) == 1
    err = state["errors"][0]
    assert err["node_name"] == "sample_logs"
    assert err["message"] == "ES 样本查询失败"
    assert err["recorded_at"]
    _assert_no_placeholder(err)


# ---------------------------------------------------------------------------
# graph_scheduled（mock 聚合/搜索/证据/报告）
# ---------------------------------------------------------------------------


def test_run_scheduled_subgraph_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_subgraph_mocks(monkeypatch)

    result = run_scheduled_subgraph(time_window=dict(_TIME_WINDOW))

    assert result["ok"] is True
    assert result["report"]["report_type"] == "periodic"
    assert result["report"]["title"] == "测试周期报告"
    assert len(result["node_trace"]) == 6
    node_names = [entry["node_name"] for entry in result["node_trace"]]
    assert node_names == [
        "build_time_window",
        "plan_queries",
        "aggregate_metrics",
        "sample_logs",
        "build_evidence",
        "generate_report",
    ]
    assert all(entry["status"] == "success" for entry in result["node_trace"])
    _assert_no_placeholder(result)


def test_run_scheduled_subgraph_generate_report_degraded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_subgraph_mocks(monkeypatch)

    def _raise_llm(_pkg: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("LLM 不可用")

    monkeypatch.setattr(
        "app.services.analysis.graph_scheduled.generate_periodic_report",
        _raise_llm,
    )

    result = run_scheduled_subgraph(time_window=dict(_TIME_WINDOW))

    assert result["ok"] is True
    assert result["report"]["degraded"] is True
    assert result["report"]["report_type"] == "periodic"
    assert any(err["node_name"] == "generate_report" for err in result["errors"])
    generate_trace = next(
        t for t in result["node_trace"] if t["node_name"] == "generate_report"
    )
    assert generate_trace["status"] == "failed"
    _assert_no_placeholder(result)


# ---------------------------------------------------------------------------
# scheduler.run_once 闭环
# ---------------------------------------------------------------------------


def test_run_once_closed_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    main_graph_calls: list[dict[str, Any]] = []

    def _mock_main_graph(trigger_type: str, **kwargs: Any) -> dict[str, Any]:
        assert trigger_type == "scheduled"
        main_graph_calls.append(kwargs)
        return {
            "ok": True,
            "report_id": "persisted-rpt-001",
            "alert_id": None,
            "node_trace": [
                {"node_name": "build_time_window", "status": "success"},
                {"node_name": "generate_report", "status": "success"},
            ],
            "alert_decision": {},
            "errors": [],
        }

    monkeypatch.setattr(
        "app.services.analysis.scheduler.run_main_graph",
        _mock_main_graph,
    )

    result = run_once(time_window=dict(_TIME_WINDOW))

    assert result["ok"] is True
    assert result["report_id"] == "persisted-rpt-001"
    assert len(result["node_trace"]) == 2
    assert len(main_graph_calls) == 1
    assert main_graph_calls[0].get("time_window") == _TIME_WINDOW
    _assert_no_placeholder(result)


def test_run_once_subgraph_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.analysis.scheduler.run_main_graph",
        lambda trigger_type, **kwargs: {
            "ok": False,
            "report_id": None,
            "alert_id": None,
            "node_trace": [{"node_name": "build_time_window", "status": "failed"}],
            "errors": [{"node_name": "build_time_window", "message": "窗口无效"}],
            "alert_decision": {},
        },
    )

    result = run_once()

    assert result["ok"] is False
    assert result["report_id"] is None
    assert "error" in result
    _assert_no_placeholder(result)
