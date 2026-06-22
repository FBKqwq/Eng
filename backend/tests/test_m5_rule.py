"""M5-09：规则闭环单元测试（全程 mock ES/LLM/子图依赖，不联网）。"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.alert import alert_service, dedup
from app.services.analysis.graph_rule import _compile_rule_graph, run_rule_subgraph
from app.services.analysis.trigger_scanner import scan_once
from app.services.diagnosis.rule_definitions import get_rule_definitions
from app.services.diagnosis.rule_engine import classify_by_rules, match_log

_PATCH_ALERT_ES = "app.services.alert.alert_service.get_es_client"
_PATCH_DEDUP_ES = "app.services.alert.dedup.get_es_client"

_PAY_FAIL_LOG: dict[str, Any] = {
    "log_id": "log-pay-001",
    "log_level": "ERROR",
    "service_name": "payment-service",
    "error_code": "PAY_FAIL",
    "trace_id": "trace-pay-001",
    "timestamp": "2026-06-22T10:30:00Z",
    "message": "支付失败",
}

_NORMAL_LOG: dict[str, Any] = {
    "log_id": "log-normal-001",
    "log_level": "INFO",
    "service_name": "order-service",
    "message": "订单创建成功",
    "timestamp": "2026-06-22T10:30:00Z",
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
    "payload": {"error_code": "PAY_FAIL", "trace_id": "trace-pay-001"},
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
    options_client.update.return_value = {"result": "updated"}
    return client


def _make_es_client_for_search(
    *,
    items: list[dict[str, Any]] | None = None,
) -> MagicMock:
    hits = [
        {
            "_id": item.get("alert_id", f"id-{idx}"),
            "_index": f"alerts-{item.get('created_at', '2026-06-22')[:10]}",
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


def _mock_context_available(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "available": True,
        "error": None,
        "items": items or [_PAY_FAIL_LOG],
        "total": len(items or [_PAY_FAIL_LOG]),
    }


def _mock_evidence(logs: list[dict[str, Any]], metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "evidence_package": {
            "summary": {"total_logs": len(logs), "error_count": 1, "warn_count": 0},
            "grouped": {"by_service": {"payment-service": 1}},
            "samples": logs[:1],
            "metrics": metrics,
        },
        "input_log_count": len(logs),
        "sampled_count": min(len(logs), 1),
    }


def _mock_diagnosis(_pkg: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "degraded": False,
        "root_cause": "支付网关超时",
        "confidence": 0.85,
        "severity": "high",
        "affected_services": ["payment-service"],
        "evidence_refs": ["log-pay-001"],
        "action_suggestions": ["检查支付网关连通性"],
    }


def _install_rule_subgraph_mocks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.analysis.graph_rule.get_trace_context",
        lambda trace_id, limit=50: _mock_context_available(),
    )
    monkeypatch.setattr(
        "app.services.analysis.graph_rule.get_service_window",
        lambda service, start, end, limit=50: _mock_context_available(),
    )
    monkeypatch.setattr(
        "app.services.analysis.graph_rule.get_similar_errors",
        lambda error_code, start, end, limit=50: _mock_context_available(),
    )
    monkeypatch.setattr(
        "app.services.analysis.graph_rule.build_evidence_package",
        _mock_evidence,
    )
    monkeypatch.setattr(
        "app.services.analysis.graph_rule.infer_root_cause",
        _mock_diagnosis,
    )
    monkeypatch.setattr(
        "app.services.analysis.graph_rule.generate_event_report",
        lambda pkg: dict(_EVENT_REPORT),
    )
    _compile_rule_graph.cache_clear()


# ---------------------------------------------------------------------------
# rule_definitions
# ---------------------------------------------------------------------------


def test_rule_definitions_three_kinds_and_pay_fail_subgraph() -> None:
    rules = get_rule_definitions()

    assert len(rules) == 10
    kinds = {rule["kind"] for rule in rules}
    assert kinds == {"error_code", "threshold", "frequency"}

    pay_fail = next(r for r in rules if r["rule_id"] == "R_PAY_FAIL")
    assert pay_fail["match"]["error_code"] == "PAY_FAIL"
    assert pay_fail["trigger_subgraph"] is True
    assert pay_fail["severity"] == "high"


# ---------------------------------------------------------------------------
# rule_engine
# ---------------------------------------------------------------------------


def test_match_log_pay_fail_matched() -> None:
    result = match_log(_PAY_FAIL_LOG)

    assert result["ok"] is True
    assert result["matched"] is True
    assert result["rule_id"] == "R_PAY_FAIL"
    assert result["rule_name"] == "支付失败"
    assert result["trigger_subgraph"] is True
    assert result["severity"] == "high"
    assert result["log_event_id"] == "log-pay-001"
    _assert_no_placeholder(result)


def test_match_log_unmatched() -> None:
    result = match_log(_NORMAL_LOG)

    assert result["ok"] is True
    assert result["matched"] is False
    assert result["rule_id"] is None
    assert result["trigger_subgraph"] is False
    _assert_no_placeholder(result)


def test_match_log_status_5xx_threshold() -> None:
    log_event = {
        "log_id": "log-5xx-001",
        "service_name": "api-gateway",
        "status_code": 503,
        "timestamp": "2026-06-22T10:30:00Z",
    }
    result = match_log(log_event)

    assert result["matched"] is True
    assert result["rule_id"] == "R_STATUS_CODE_5XX"
    assert result["trigger_subgraph"] is True
    _assert_no_placeholder(result)


def test_classify_by_rules_compatibility() -> None:
    pay_result = classify_by_rules("支付 pay_fail 异常")
    assert pay_result["route"] == "rule"
    assert pay_result["anomaly_type"] == "支付异常"
    assert pay_result["severity"] == "high"

    timeout_result = classify_by_rules("接口 timeout 超时")
    assert timeout_result["route"] == "rule"
    assert timeout_result["anomaly_type"] == "接口超时"

    unknown_result = classify_by_rules("随机未知关键词")
    assert unknown_result["route"] == "llm_pending"
    assert unknown_result["anomaly_type"] == "未知异常"
    _assert_no_placeholder(unknown_result)


# ---------------------------------------------------------------------------
# alert_service（mock ES）
# ---------------------------------------------------------------------------


def test_write_alert_success(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_es_client_for_write()
    monkeypatch.setattr(_PATCH_ALERT_ES, lambda: client)

    result = alert_service.write_alert(
        {
            "alert_type": "pay_fail",
            "severity": "high",
            "title": "支付失败预警",
            "affected_service": "payment-service",
        }
    )

    assert result["ok"] is True
    assert result["alert_id"]
    options_client = client.options.return_value
    options_client.index.assert_called_once()
    doc = options_client.index.call_args.kwargs["document"]
    assert doc["status"] == alert_service.STATUS_ACTIVE
    assert doc["alert_type"] == "pay_fail"
    assert doc["evidence_count"] == 1
    _assert_no_placeholder(result)


def test_list_active_alerts_success(monkeypatch: pytest.MonkeyPatch) -> None:
    items = [
        {
            "alert_id": "alert-001",
            "alert_type": "pay_fail",
            "severity": "high",
            "status": "active",
            "title": "支付失败",
            "affected_service": "payment-service",
            "evidence_count": 2,
            "created_at": "2026-06-22T12:00:00Z",
            "updated_at": "2026-06-22T12:05:00Z",
        }
    ]
    monkeypatch.setattr(_PATCH_ALERT_ES, lambda: _make_es_client_for_search(items=items))

    result = alert_service.list_active_alerts(limit=10)

    assert result["ok"] is True
    assert result["total"] == 1
    assert result["limit"] == 10
    assert len(result["items"]) == 1
    assert result["items"][0]["alert_id"] == "alert-001"
    assert result["items"][0]["status"] == "active"
    _assert_no_placeholder(result)


def test_acknowledge_alert_state_machine(monkeypatch: pytest.MonkeyPatch) -> None:
    active_doc = {
        "alert_id": "alert-ack-001",
        "alert_type": "pay_fail",
        "severity": "high",
        "status": "active",
        "title": "待确认预警",
        "evidence_count": 1,
        "created_at": "2026-06-22T12:00:00Z",
        "updated_at": "2026-06-22T12:00:00Z",
        "payload": {},
    }
    client = _make_es_client_for_search(items=[active_doc])
    monkeypatch.setattr(_PATCH_ALERT_ES, lambda: client)

    result = alert_service.acknowledge_alert("alert-ack-001", operator="ops-user")

    assert result["ok"] is True
    assert result["alert_id"] == "alert-ack-001"
    assert result["status"] == alert_service.STATUS_ACKNOWLEDGED
    options_client = client.options.return_value
    options_client.update.assert_called_once()
    update_doc = options_client.update.call_args.kwargs["doc"]
    assert update_doc["status"] == alert_service.STATUS_ACKNOWLEDGED
    assert update_doc["payload"]["acknowledged_by"] == "ops-user"
    assert "acknowledged_at" in update_doc["payload"]
    _assert_no_placeholder(result)


# ---------------------------------------------------------------------------
# dedup（mock ES）
# ---------------------------------------------------------------------------


def test_build_idempotency_key_stable() -> None:
    candidate = {
        "alert_type": "pay_fail",
        "affected_service": "payment-service",
        "created_at": "2026-06-22T10:35:00Z",
    }
    key_a = dedup.build_idempotency_key(candidate, bucket_minutes=10)
    key_b = dedup.build_idempotency_key(candidate, bucket_minutes=10)

    assert key_a == key_b
    assert key_a.startswith("pay_fail:payment-service:")
    assert "2026-06-22T10:30:00Z" in key_a


def test_check_duplicate_not_duplicate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_PATCH_DEDUP_ES, lambda: _make_es_client_for_search(items=[]))

    result = dedup.check_duplicate(_ALERT_CANDIDATE)

    assert result["ok"] is True
    assert result["is_duplicate"] is False
    assert result["existing_alert_id"] is None
    assert result["idempotency_key"]
    _assert_no_placeholder(result)


def test_check_duplicate_is_duplicate(monkeypatch: pytest.MonkeyPatch) -> None:
    existing = {
        "alert_id": "alert-existing-001",
        "alert_type": "pay_fail",
        "status": "active",
        "affected_service": "payment-service",
        "created_at": "2026-06-22T10:32:00Z",
    }
    monkeypatch.setattr(_PATCH_DEDUP_ES, lambda: _make_es_client_for_search(items=[existing]))

    result = dedup.check_duplicate(_ALERT_CANDIDATE)

    assert result["ok"] is True
    assert result["is_duplicate"] is True
    assert result["existing_alert_id"] == "alert-existing-001"
    assert result["idempotency_key"]
    _assert_no_placeholder(result)


# ---------------------------------------------------------------------------
# graph_rule（mock 上下文/证据/LLM）
# ---------------------------------------------------------------------------


def test_run_rule_subgraph_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_rule_subgraph_mocks(monkeypatch)

    result = run_rule_subgraph(dict(_PAY_FAIL_LOG))

    assert result["ok"] is True
    assert result["report"]["report_type"] == "event"
    assert result["report"]["title"] == "支付失败：payment-service"
    assert result["alert_candidate"]["alert_type"] == "pay_fail"
    assert result["alert_candidate"]["affected_service"] == "payment-service"
    assert len(result["node_trace"]) == 7
    node_names = [entry["node_name"] for entry in result["node_trace"]]
    assert node_names == [
        "parse_trigger_event",
        "fetch_context",
        "correlate_events",
        "build_evidence",
        "infer_root_cause",
        "assess_severity",
        "generate_event_report",
    ]
    assert all(entry["status"] == "success" for entry in result["node_trace"])
    _assert_no_placeholder(result)


def test_run_rule_subgraph_infer_root_cause_degraded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_rule_subgraph_mocks(monkeypatch)

    def _raise_llm(_pkg: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("LLM 不可用")

    monkeypatch.setattr(
        "app.services.analysis.graph_rule.infer_root_cause",
        _raise_llm,
    )

    result = run_rule_subgraph(dict(_PAY_FAIL_LOG))

    assert result["ok"] is True
    assert result["report"]["report_type"] == "event"
    assert any(err["node_name"] == "infer_root_cause" for err in result["errors"])
    infer_trace = next(
        t for t in result["node_trace"] if t["node_name"] == "infer_root_cause"
    )
    assert infer_trace["status"] == "failed"
    assert result["alert_candidate"]["severity"] == "high"
    generate_trace = next(
        t for t in result["node_trace"] if t["node_name"] == "generate_event_report"
    )
    assert generate_trace["status"] == "success"
    _assert_no_placeholder(result)


def test_run_rule_subgraph_generate_report_degraded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_rule_subgraph_mocks(monkeypatch)

    def _raise_report(_pkg: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("报告生成失败")

    monkeypatch.setattr(
        "app.services.analysis.graph_rule.generate_event_report",
        _raise_report,
    )

    result = run_rule_subgraph(dict(_PAY_FAIL_LOG))

    assert result["ok"] is True
    assert result["report"]["degraded"] is True
    assert any(err["node_name"] == "generate_event_report" for err in result["errors"])
    report_trace = next(
        t for t in result["node_trace"] if t["node_name"] == "generate_event_report"
    )
    assert report_trace["status"] == "failed"
    _assert_no_placeholder(result)


# ---------------------------------------------------------------------------
# trigger_scanner.scan_once 闭环
# ---------------------------------------------------------------------------


def test_scan_once_closed_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    main_graph_calls: list[dict[str, Any]] = []

    def _mock_search(request: Any) -> dict[str, Any]:
        return {
            "available": True,
            "error": None,
            "items": [dict(_PAY_FAIL_LOG)],
            "total": 1,
            "page": request.page,
            "page_size": request.page_size,
            "has_more": False,
            "took_ms": 3,
        }

    def _mock_main_graph(trigger_type: str, **kwargs: Any) -> dict[str, Any]:
        assert trigger_type == "rule"
        main_graph_calls.append(kwargs)
        return {
            "ok": True,
            "report_id": "rpt-rule-001",
            "alert_id": "alert-new-001",
            "node_trace": [{"node_name": "parse_trigger_event", "status": "success"}],
            "alert_decision": {"should_alert": True},
            "errors": [],
        }

    monkeypatch.setattr(
        "app.services.analysis.trigger_scanner.log_query_service.search_logs",
        _mock_search,
    )
    monkeypatch.setattr(
        "app.services.analysis.trigger_scanner.run_main_graph",
        _mock_main_graph,
    )

    result = scan_once()

    assert result["ok"] is True
    assert result["triggered_count"] == 1
    assert result["report_ids"] == ["rpt-rule-001"]
    assert result["alert_ids"] == ["alert-new-001"]
    assert len(main_graph_calls) == 1
    assert "trigger_event" in main_graph_calls[0]
    _assert_no_placeholder(result)


def test_scan_once_dedup_increments_existing_alert(monkeypatch: pytest.MonkeyPatch) -> None:
    def _mock_search(request: Any) -> dict[str, Any]:
        return {
            "available": True,
            "error": None,
            "items": [dict(_PAY_FAIL_LOG)],
            "total": 1,
            "page": request.page,
            "page_size": request.page_size,
            "has_more": False,
            "took_ms": 3,
        }

    def _mock_main_graph(trigger_type: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "ok": True,
            "report_id": "rpt-dedup-001",
            "alert_id": "alert-existing-001",
            "node_trace": [],
            "alert_decision": {
                "should_alert": True,
                "is_duplicate": True,
                "existing_alert_id": "alert-existing-001",
            },
            "errors": [],
        }

    monkeypatch.setattr(
        "app.services.analysis.trigger_scanner.log_query_service.search_logs",
        _mock_search,
    )
    monkeypatch.setattr(
        "app.services.analysis.trigger_scanner.run_main_graph",
        _mock_main_graph,
    )

    result = scan_once()

    assert result["ok"] is True
    assert result["triggered_count"] == 1
    assert result["alert_ids"] == ["alert-existing-001"]
    assert result["report_ids"] == ["rpt-dedup-001"]
    _assert_no_placeholder(result)
