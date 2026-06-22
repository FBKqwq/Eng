"""M6-06：主图与 alert_chain 单元测试（全程 mock ES/LLM/子图，不联网）。"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
import fastapi.routing
import starlette.routing

# FastAPI 0.116 与 Starlette 1.3+ 生命周期 API 不兼容；测试层做最小兼容垫片
_router_init = starlette.routing.Router.__init__


def _router_init_compat(self, *args: Any, **kwargs: Any) -> None:
    kwargs.pop("on_startup", None)
    kwargs.pop("on_shutdown", None)
    return _router_init(self, *args, **kwargs)


starlette.routing.Router.__init__ = _router_init_compat  # type: ignore[method-assign]

_api_router_init = fastapi.routing.APIRouter.__init__


def _api_router_init_compat(self, *args: Any, **kwargs: Any) -> None:
    _api_router_init(self, *args, **kwargs)
    if not hasattr(self, "on_startup"):
        self.on_startup = []
    if not hasattr(self, "on_shutdown"):
        self.on_shutdown = []


fastapi.routing.APIRouter.__init__ = _api_router_init_compat  # type: ignore[method-assign]

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app
from app.services.langchain import llm_manager
from app.services.langchain.alert_chain import explain_alert

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

_EVENT_REPORT: dict[str, Any] = {
    "ok": True,
    "degraded": False,
    "report_type": "event",
    "title": "支付失败：payment-service",
    "severity": "high",
    "summary": "支付网关超时导致 PAY_FAIL",
    "root_cause": "支付网关超时",
    "key_findings": ["PAY_FAIL 错误码集中出现"],
    "recommendations": ["检查支付网关连通性"],
}

_ALERT_CANDIDATE: dict[str, Any] = {
    "alert_type": "pay_fail",
    "severity": "high",
    "title": "支付失败：payment-service",
    "affected_service": "payment-service",
    "description": "支付网关超时",
    "created_at": "2026-06-22T10:30:00Z",
    "trigger_log_id": "log-pay-001",
    "rule_id": "R_PAY_FAIL",
    "payload": {"error_code": "PAY_FAIL"},
}

_PAY_FAIL_LOG: dict[str, Any] = {
    "log_id": "log-pay-001",
    "log_level": "ERROR",
    "service_name": "payment-service",
    "error_code": "PAY_FAIL",
    "timestamp": "2026-06-22T10:30:00Z",
    "message": "支付失败",
}

_ALERT_LLM_DATA: dict[str, Any] = {
    "title": "支付服务高风险预警",
    "description": "检测到支付失败集中爆发",
    "severity": "high",
    "impact_scope": ["payment-service"],
    "suggested_actions": ["检查支付网关"],
    "evidence_summary": "PAY_FAIL 错误码激增",
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


def _install_persist_mocks(
    monkeypatch: pytest.MonkeyPatch,
    *,
    write_report_calls: list[dict[str, Any]] | None = None,
    write_alert_calls: list[dict[str, Any]] | None = None,
    dedup_result: dict[str, Any] | None = None,
) -> None:
    report_calls = write_report_calls if write_report_calls is not None else []
    alert_calls = write_alert_calls if write_alert_calls is not None else []
    dedup = dedup_result or {
        "ok": True,
        "is_duplicate": False,
        "existing_alert_id": None,
        "idempotency_key": "pay_fail:payment-service:2026-06-22T10:30:00Z",
    }

    def _mock_write_report(report: dict[str, Any]) -> dict[str, Any]:
        report_calls.append(report)
        return {"ok": True, "report_id": f"rpt-{len(report_calls):03d}"}

    def _mock_write_alert(alert: dict[str, Any]) -> dict[str, Any]:
        alert_calls.append(alert)
        existing = alert.get("existing_alert_id")
        return {"ok": True, "alert_id": existing or f"alert-{len(alert_calls):03d}"}

    monkeypatch.setattr(
        "app.services.analysis.graph_main.write_report",
        _mock_write_report,
    )
    monkeypatch.setattr(
        "app.services.analysis.graph_main.write_alert",
        _mock_write_alert,
    )
    monkeypatch.setattr(
        "app.services.analysis.graph_main.check_duplicate",
        lambda _candidate: dict(dedup),
    )


def _mock_scheduled_subgraph_ok(*, time_window: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "report": dict(_PERIODIC_REPORT),
        "node_trace": [
            {"node_name": "build_time_window", "status": "success", "duration_ms": 5},
            {"node_name": "generate_report", "status": "success", "duration_ms": 10},
        ],
        "errors": [],
    }


def _mock_rule_subgraph_ok(*, trigger_event: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "report": dict(_EVENT_REPORT),
        "alert_candidate": dict(_ALERT_CANDIDATE),
        "node_trace": [
            {"node_name": "parse_trigger_event", "status": "success", "duration_ms": 3},
            {"node_name": "generate_event_report", "status": "success", "duration_ms": 8},
        ],
        "errors": [],
    }


# ---------------------------------------------------------------------------
# alert_chain
# ---------------------------------------------------------------------------


def test_explain_alert_llm_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """LLM 可用且解析成功时返回非降级预警文案。"""
    monkeypatch.setattr(llm_manager, "is_llm_available", lambda: True)
    monkeypatch.setattr(
        llm_manager,
        "invoke_structured",
        lambda task, prompt, schema: {"ok": True, "data": _ALERT_LLM_DATA},
    )

    result = explain_alert(dict(_ALERT_CANDIDATE))

    assert result["ok"] is True
    assert result["degraded"] is False
    assert result["title"] == "支付服务高风险预警"
    assert "支付失败" in result["detail"] or "PAY_FAIL" in result["detail"]
    _assert_no_placeholder(result)


def test_explain_alert_degraded_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """LLM 不可用时走 alert_type/service/severity 模板降级。"""
    monkeypatch.setattr(llm_manager, "is_llm_available", lambda: False)

    result = explain_alert(dict(_ALERT_CANDIDATE))

    assert result["ok"] is True
    assert result["degraded"] is True
    assert "payment-service" in result["title"]
    assert "规则模板" in result["detail"]
    _assert_no_placeholder(result)


# ---------------------------------------------------------------------------
# graph_main — 路由与子图
# ---------------------------------------------------------------------------


def test_run_main_graph_scheduled_route(monkeypatch: pytest.MonkeyPatch) -> None:
    """scheduled 触发类型走定时子图并完成主图收口。"""
    write_calls: list[dict[str, Any]] = []
    _install_persist_mocks(monkeypatch, write_report_calls=write_calls)
    monkeypatch.setattr(
        "app.services.analysis.graph_main.run_scheduled_subgraph",
        _mock_scheduled_subgraph_ok,
    )
    monkeypatch.setattr(llm_manager, "is_llm_available", lambda: False)

    from app.services.analysis.graph_main import run_main_graph

    result = run_main_graph("scheduled", time_window=dict(_TIME_WINDOW))

    assert result["ok"] is True
    assert result["report_id"] == "rpt-001"
    node_names = [e["node_name"] for e in result["node_trace"]]
    assert "run_scheduled_subgraph" in node_names
    assert "run_rule_subgraph" not in node_names
    assert "merge_result" in node_names
    assert "alert_decision" in node_names
    assert "persist_result" in node_names
    assert result["alert_decision"]["should_alert"] is False
    assert len(write_calls) == 1
    _assert_no_placeholder(result)


def test_run_main_graph_rule_route(monkeypatch: pytest.MonkeyPatch) -> None:
    """rule 触发类型走规则子图并完成主图收口。"""
    write_report_calls: list[dict[str, Any]] = []
    write_alert_calls: list[dict[str, Any]] = []
    _install_persist_mocks(
        monkeypatch,
        write_report_calls=write_report_calls,
        write_alert_calls=write_alert_calls,
    )
    monkeypatch.setattr(
        "app.services.analysis.graph_main.run_rule_subgraph",
        _mock_rule_subgraph_ok,
    )
    monkeypatch.setattr(llm_manager, "is_llm_available", lambda: False)

    from app.services.analysis.graph_main import run_main_graph

    result = run_main_graph("rule", trigger_event=dict(_PAY_FAIL_LOG))

    assert result["ok"] is True
    assert result["report_id"] == "rpt-001"
    assert result["alert_id"] == "alert-001"
    node_names = [e["node_name"] for e in result["node_trace"]]
    assert "run_rule_subgraph" in node_names
    assert "run_scheduled_subgraph" not in node_names
    assert result["alert_decision"]["should_alert"] is True
    assert len(write_report_calls) == 1
    assert len(write_alert_calls) == 1
    _assert_no_placeholder(result)


def test_run_main_graph_invalid_trigger_skips_subgraph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """无效 trigger_type 路由到 merge，子图不被调用。"""
    scheduled_called = False
    rule_called = False
    write_calls: list[dict[str, Any]] = []
    _install_persist_mocks(monkeypatch, write_report_calls=write_calls)

    def _scheduled(**_: Any) -> dict[str, Any]:
        nonlocal scheduled_called
        scheduled_called = True
        return _mock_scheduled_subgraph_ok()

    def _rule(**_: Any) -> dict[str, Any]:
        nonlocal rule_called
        rule_called = True
        return _mock_rule_subgraph_ok()

    monkeypatch.setattr("app.services.analysis.graph_main.run_scheduled_subgraph", _scheduled)
    monkeypatch.setattr("app.services.analysis.graph_main.run_rule_subgraph", _rule)

    from app.services.analysis.graph_main import run_main_graph

    result = run_main_graph("manual", time_window=dict(_TIME_WINDOW))

    assert scheduled_called is False
    assert rule_called is False
    assert result["ok"] is True
    assert any(err.get("node_name") == "normalize_trigger" for err in result["errors"])
    merged_report = write_calls[0]
    assert merged_report.get("degraded") is True
    _assert_no_placeholder(result)


# ---------------------------------------------------------------------------
# graph_main — merge / alert_decision / persist
# ---------------------------------------------------------------------------


def test_run_main_graph_merge_normalizes_report(monkeypatch: pytest.MonkeyPatch) -> None:
    """merge_result 将子图报告归一化并合并子图 node_trace。"""
    write_calls: list[dict[str, Any]] = []
    _install_persist_mocks(monkeypatch, write_report_calls=write_calls)
    monkeypatch.setattr(
        "app.services.analysis.graph_main.run_scheduled_subgraph",
        _mock_scheduled_subgraph_ok,
    )
    monkeypatch.setattr(llm_manager, "is_llm_available", lambda: False)

    from app.services.analysis.graph_main import run_main_graph

    result = run_main_graph("scheduled", time_window=dict(_TIME_WINDOW))

    persisted = write_calls[0]
    assert persisted["report_type"] == "periodic"
    assert persisted["trigger_type"] == "scheduled"
    assert persisted["task_id"]
    assert isinstance(persisted.get("node_trace"), list)
    subgraph_traces = [
        e["node_name"]
        for e in persisted["node_trace"]
        if str(e.get("node_name", "")).startswith("scheduled.")
    ]
    assert "scheduled.build_time_window" in subgraph_traces
    _assert_no_placeholder(result)


def test_run_main_graph_rule_alert_high_severity(monkeypatch: pytest.MonkeyPatch) -> None:
    """规则路径 severity≥high 时 alert_decision 应出预警。"""
    _install_persist_mocks(monkeypatch)
    monkeypatch.setattr(
        "app.services.analysis.graph_main.run_rule_subgraph",
        _mock_rule_subgraph_ok,
    )
    monkeypatch.setattr(llm_manager, "is_llm_available", lambda: False)

    from app.services.analysis.graph_main import run_main_graph

    result = run_main_graph("rule", trigger_event=dict(_PAY_FAIL_LOG))

    decision = result["alert_decision"]
    assert decision["should_alert"] is True
    assert decision["is_duplicate"] is False
    assert decision["alert_candidate"]["alert_type"] == "pay_fail"
    assert decision["explanation"]["ok"] is True
    _assert_no_placeholder(result)


def test_run_main_graph_scheduled_risk_high_alert(monkeypatch: pytest.MonkeyPatch) -> None:
    """定时路径 risk_level=high 时生成周期预警候选。"""
    high_risk_report = dict(_PERIODIC_REPORT)
    high_risk_report["risk_level"] = "high"
    high_risk_report["title"] = "周期体检高风险"

    def _high_risk_subgraph(**_: Any) -> dict[str, Any]:
        return {
            "ok": True,
            "report": high_risk_report,
            "node_trace": [{"node_name": "generate_report", "status": "success"}],
            "errors": [],
        }

    write_alert_calls: list[dict[str, Any]] = []
    _install_persist_mocks(monkeypatch, write_alert_calls=write_alert_calls)
    monkeypatch.setattr(
        "app.services.analysis.graph_main.run_scheduled_subgraph",
        _high_risk_subgraph,
    )
    monkeypatch.setattr(llm_manager, "is_llm_available", lambda: False)

    from app.services.analysis.graph_main import run_main_graph

    result = run_main_graph("scheduled", time_window=dict(_TIME_WINDOW))

    assert result["alert_decision"]["should_alert"] is True
    assert result["alert_decision"]["alert_candidate"]["alert_type"] == "periodic_risk_high"
    assert len(write_alert_calls) == 1
    _assert_no_placeholder(result)


def test_run_main_graph_alert_dedup_hit(monkeypatch: pytest.MonkeyPatch) -> None:
    """去重命中时 alert_decision 标记 is_duplicate 并复用 existing_alert_id。"""
    write_alert_calls: list[dict[str, Any]] = []
    _install_persist_mocks(
        monkeypatch,
        write_alert_calls=write_alert_calls,
        dedup_result={
            "ok": True,
            "is_duplicate": True,
            "existing_alert_id": "alert-existing-001",
            "idempotency_key": "pay_fail:payment-service:2026-06-22T10:30:00Z",
        },
    )
    monkeypatch.setattr(
        "app.services.analysis.graph_main.run_rule_subgraph",
        _mock_rule_subgraph_ok,
    )
    monkeypatch.setattr(llm_manager, "is_llm_available", lambda: False)

    from app.services.analysis.graph_main import run_main_graph

    result = run_main_graph("rule", trigger_event=dict(_PAY_FAIL_LOG))

    decision = result["alert_decision"]
    assert decision["should_alert"] is True
    assert decision["is_duplicate"] is True
    assert decision["existing_alert_id"] == "alert-existing-001"
    assert result["alert_id"] == "alert-existing-001"
    assert len(write_alert_calls) == 1
    assert write_alert_calls[0]["existing_alert_id"] == "alert-existing-001"
    _assert_no_placeholder(result)


def test_run_main_graph_persist_only_in_persist_node(monkeypatch: pytest.MonkeyPatch) -> None:
    """write_report/write_alert 仅在 persist_result 收口调用一次。"""
    write_report_calls: list[dict[str, Any]] = []
    write_alert_calls: list[dict[str, Any]] = []
    _install_persist_mocks(
        monkeypatch,
        write_report_calls=write_report_calls,
        write_alert_calls=write_alert_calls,
    )
    monkeypatch.setattr(
        "app.services.analysis.graph_main.run_rule_subgraph",
        _mock_rule_subgraph_ok,
    )
    monkeypatch.setattr(llm_manager, "is_llm_available", lambda: False)

    from app.services.analysis.graph_main import run_main_graph

    result = run_main_graph("rule", trigger_event=dict(_PAY_FAIL_LOG))

    assert len(write_report_calls) == 1
    assert len(write_alert_calls) == 1
    persist_trace = next(
        e for e in result["node_trace"] if e.get("node_name") == "persist_result"
    )
    assert persist_trace["status"] == "success"
    assert "node_trace" in write_report_calls[0]
    _assert_no_placeholder(result)


def test_run_main_graph_subgraph_failure_degraded(monkeypatch: pytest.MonkeyPatch) -> None:
    """子图异常时 errors 非空且整图不崩溃。"""
    write_calls: list[dict[str, Any]] = []
    _install_persist_mocks(monkeypatch, write_report_calls=write_calls)

    def _failing_subgraph(**_: Any) -> dict[str, Any]:
        raise RuntimeError("子图执行失败")

    monkeypatch.setattr(
        "app.services.analysis.graph_main.run_scheduled_subgraph",
        _failing_subgraph,
    )

    from app.services.analysis.graph_main import run_main_graph

    result = run_main_graph("scheduled", time_window=dict(_TIME_WINDOW))

    assert any(err.get("node_name") == "run_scheduled_subgraph" for err in result["errors"])
    failed_trace = next(
        e for e in result["node_trace"] if e.get("node_name") == "run_scheduled_subgraph"
    )
    assert failed_trace["status"] == "failed"
    assert result["ok"] is True
    assert write_calls[0].get("degraded") is True
    _assert_no_placeholder(result)


# ---------------------------------------------------------------------------
# analysis API
# ---------------------------------------------------------------------------


def test_analysis_api_runs_recent(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /analysis/runs/recent 返回 node_trace 摘要。"""
    list_item = {
        "report_id": "rpt-api-001",
        "report_type": "periodic",
        "title": "API 测试报告",
        "created_at": "2026-06-22T12:00:00Z",
    }
    full_report = {
        **list_item,
        "trigger_type": "scheduled",
        "node_trace": [
            {
                "node_name": "normalize_trigger",
                "status": "success",
                "duration_ms": 2,
                "output_summary": "触发类型 scheduled",
            },
            {
                "node_name": "persist_result",
                "status": "success",
                "duration_ms": 5,
                "output_summary": "report=rpt-api",
            },
        ],
    }

    monkeypatch.setattr(
        "app.api.v1.analysis.list_recent_reports",
        lambda limit=20: {"ok": True, "items": [list_item], "total": 1, "limit": limit},
    )
    monkeypatch.setattr(
        "app.api.v1.analysis.get_report",
        lambda report_id: {"ok": True, "report_id": report_id, "report": full_report},
    )

    client = TestClient(app)
    response = client.get("/api/v1/analysis/runs/recent?limit=5")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["total"] == 1
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["report_id"] == "rpt-api-001"
    assert item["node_count"] == 2
    assert item["total_duration_ms"] == 7
    assert item["node_trace"][0]["node_name"] == "normalize_trigger"
    _assert_no_placeholder(body)


def test_analysis_api_run_manual_trigger(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /analysis/run 手动触发主图并返回 node_trace。"""
    mock_trace = [
        {"node_name": "normalize_trigger", "status": "success", "duration_ms": 1},
        {"node_name": "persist_result", "status": "success", "duration_ms": 3},
    ]

    def _mock_run_main_graph(trigger_type: str, **kwargs: Any) -> dict[str, Any]:
        assert trigger_type == "rule"
        assert kwargs.get("trigger_event", {}).get("log_id") == "log-pay-001"
        return {
            "ok": True,
            "report_id": "rpt-manual-001",
            "alert_id": "alert-manual-001",
            "node_trace": mock_trace,
            "alert_decision": {"should_alert": True, "is_duplicate": False},
            "errors": [],
        }

    monkeypatch.setattr("app.api.v1.analysis.run_main_graph", _mock_run_main_graph)

    client = TestClient(app)
    response = client.post(
        "/api/v1/analysis/run",
        json={
            "trigger_type": "rule",
            "trigger_event": dict(_PAY_FAIL_LOG),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["report_id"] == "rpt-manual-001"
    assert body["alert_id"] == "alert-manual-001"
    assert len(body["node_trace"]) == 2
    assert body["alert_decision"]["should_alert"] is True
    _assert_no_placeholder(body)
