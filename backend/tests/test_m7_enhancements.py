"""M7-09：M7 增强项单测（关系发现、七节点子图、16 工具、MCP 读写分离）。

全程 monkeypatch mock ES/LLM/FastMCP，不联网、不要求安装 fastmcp。
"""

from __future__ import annotations

import sys
import types
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.analysis.graph_scheduled import run_scheduled_subgraph
from app.services.langchain.chain_schemas import RelationChainOutput, RelationItem
from app.services.langchain.relation_chain import discover_relations
from app.services.tools import alert_tools, elasticsearch_tools, kibana_tools, report_tools
from app.services.tools.registry import (
    create_mcp_server,
    get_langchain_tools,
    list_registered_tool_names,
)

_START = datetime(2026, 6, 22, 10, 0, 0)
_END = datetime(2026, 6, 22, 11, 0, 0)
_BASELINE_START = datetime(2026, 6, 21, 10, 0, 0)
_BASELINE_END = datetime(2026, 6, 21, 11, 0, 0)

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

_RELATION_LLM_DATA: dict[str, Any] = {
    "relations": [
        {
            "relation_type": "temporal_correlation",
            "description": "流量高峰后支付失败率上升",
            "entities": ["traffic_peak", "pay_fail"],
            "confidence": 0.82,
            "evidence_refs": ["metrics.traffic", "metrics.errors"],
        }
    ]
}

_FUNNEL_OK: dict[str, Any] = {
    "available": True,
    "error": None,
    "buckets": [
        {"key": "browse", "count": 100},
        {"key": "cart", "count": 60},
        {"key": "pay", "count": 40},
    ],
    "total": 200,
}

_TRAFFIC_OK: dict[str, Any] = {
    "available": True,
    "error": None,
    "buckets": [
        {"key": "2026-06-22T10:05:00", "count": 50},
        {"key": "2026-06-22T10:15:00", "count": 120},
        {"key": "2026-06-22T10:25:00", "count": 80},
    ],
    "total": 250,
}

_WRITE_TOOL_NAMES = frozenset({"analysis_write_report", "alert_write_event"})

_NEW_READ_TOOL_NAMES = frozenset(
    {
        "es_get_business_funnel",
        "es_detect_traffic_peak",
        "es_compare_time_windows",
        "kibana_generate_link",
        "report_list_recent",
        "alert_list_active",
    }
)


def _assert_no_placeholder(obj: Any) -> None:
    if isinstance(obj, dict):
        assert "placeholder" not in obj
        for value in obj.values():
            _assert_no_placeholder(value)
    elif isinstance(obj, list):
        for item in obj:
            _assert_no_placeholder(item)


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
# 关系发现 discover_relations
# ---------------------------------------------------------------------------


def test_discover_relations_llm_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.langchain.relation_chain.llm_manager.is_llm_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "app.services.langchain.relation_chain.llm_manager.invoke_structured",
        lambda task, prompt, schema: {"ok": True, "data": _RELATION_LLM_DATA},
    )

    result = discover_relations({"summary": {"total_logs": 10}})

    assert result["ok"] is True
    assert result["degraded"] is False
    assert len(result["relations"]) == 1
    assert result["relations"][0]["description"] == "流量高峰后支付失败率上升"
    _assert_no_placeholder(result)


def test_discover_relations_llm_unavailable_degraded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.langchain.relation_chain.llm_manager.is_llm_available",
        lambda: False,
    )

    result = discover_relations({"summary": {"total_logs": 5}})

    assert result == {"ok": True, "degraded": True, "relations": []}
    _assert_no_placeholder(result)


def test_discover_relations_llm_invoke_failure_degraded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.langchain.relation_chain.llm_manager.is_llm_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "app.services.langchain.relation_chain.llm_manager.invoke_structured",
        lambda *args, **kwargs: {"ok": False, "error": "parse_failed"},
    )

    result = discover_relations({"evidence_package": {"summary": {}}})

    assert result["ok"] is True
    assert result["degraded"] is True
    assert result["relations"] == []
    _assert_no_placeholder(result)


# ---------------------------------------------------------------------------
# RelationChainOutput / RelationItem schema
# ---------------------------------------------------------------------------


def test_relation_item_default_construction() -> None:
    item = RelationItem()

    assert item.relation_type == "temporal_correlation"
    assert item.description == ""
    assert item.entities == []
    assert item.confidence == 0.0
    assert item.evidence_refs == []


def test_relation_item_confidence_clamping() -> None:
    high = RelationItem(confidence=1.5)
    low = RelationItem(confidence=-0.3)
    invalid = RelationItem(confidence="not-a-number")

    assert high.confidence == 1.0
    assert low.confidence == 0.0
    assert invalid.confidence == 0.0


def test_relation_chain_output_default_empty() -> None:
    output = RelationChainOutput()

    assert output.relations == []


# ---------------------------------------------------------------------------
# 定时子图七节点 + analyze_relations
# ---------------------------------------------------------------------------


def test_scheduled_subgraph_seven_nodes_includes_analyze_relations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_subgraph_mocks(monkeypatch)

    result = run_scheduled_subgraph(time_window=dict(_TIME_WINDOW))

    assert result["ok"] is True
    assert len(result["node_trace"]) == 7
    node_names = [entry["node_name"] for entry in result["node_trace"]]
    assert node_names == [
        "build_time_window",
        "plan_queries",
        "aggregate_metrics",
        "sample_logs",
        "build_evidence",
        "analyze_relations",
        "generate_report",
    ]
    _assert_no_placeholder(result)


def test_scheduled_subgraph_relations_injected_into_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_subgraph_mocks(monkeypatch)
    relations = [
        {
            "relation_type": "causal_hypothesis",
            "description": "库存服务延迟导致下单失败",
            "entities": ["inventory-service", "order-service"],
            "confidence": 0.75,
            "evidence_refs": ["sample-1"],
        }
    ]

    def _mock_discover(_pkg: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "degraded": False, "relations": relations}

    monkeypatch.setattr(
        "app.services.analysis.graph_scheduled.discover_relations",
        _mock_discover,
    )

    result = run_scheduled_subgraph(time_window=dict(_TIME_WINDOW))

    assert result["ok"] is True
    assert result["report"]["relations"] == relations
    rel_trace = next(t for t in result["node_trace"] if t["node_name"] == "analyze_relations")
    assert rel_trace["status"] == "success"
    _assert_no_placeholder(result)


def test_scheduled_subgraph_relations_degraded_skipped_report_still_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_subgraph_mocks(monkeypatch)
    monkeypatch.setattr(
        "app.services.analysis.graph_scheduled.discover_relations",
        lambda _pkg: {"ok": True, "degraded": True, "relations": []},
    )

    result = run_scheduled_subgraph(time_window=dict(_TIME_WINDOW))

    assert result["ok"] is True
    assert result["report"]["report_type"] == "periodic"
    rel_trace = next(t for t in result["node_trace"] if t["node_name"] == "analyze_relations")
    assert rel_trace["status"] == "skipped"
    _assert_no_placeholder(result)


# ---------------------------------------------------------------------------
# ES 工具 11 / 12 / 13
# ---------------------------------------------------------------------------


def test_es_get_business_funnel_mock_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.tools.elasticsearch_tools.aggregation_service.aggregate_behavior_funnel",
        lambda **kwargs: dict(_FUNNEL_OK),
    )

    result = elasticsearch_tools.es_get_business_funnel(
        elasticsearch_tools.EsGetBusinessFunnelInput(start_time=_START, end_time=_END)
    )

    assert result["ok"] is True
    assert result["tool"] == "es_get_business_funnel"
    assert len(result["buckets"]) == 3
    _assert_no_placeholder(result)


def test_es_detect_traffic_peak_peak_bucket(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.tools.elasticsearch_tools.aggregation_service.aggregate_traffic",
        lambda **kwargs: dict(_TRAFFIC_OK),
    )

    result = elasticsearch_tools.es_detect_traffic_peak(
        elasticsearch_tools.EsDetectTrafficPeakInput(start_time=_START, end_time=_END)
    )

    assert result["ok"] is True
    assert result["tool"] == "es_detect_traffic_peak"
    assert result["peak_bucket"]["key"] == "2026-06-22T10:15:00"
    assert result["peak_bucket"]["count"] == 120
    _assert_no_placeholder(result)


def test_es_compare_time_windows_comparison_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    def _mock_invoke(
        template: str,
        *,
        start_time: datetime,
        end_time: datetime,
        interval: Any = None,
        top_n: int = 10,
    ) -> dict[str, Any]:
        if start_time == _START:
            return {
                "available": True,
                "error": None,
                "buckets": [{"key": "current", "count": 40}],
                "extra": {"total_count": 40},
            }
        return {
            "available": True,
            "error": None,
            "buckets": [{"key": "baseline", "count": 20}],
            "extra": {"total_count": 20},
        }

    monkeypatch.setattr(
        "app.services.tools.elasticsearch_tools._invoke_aggregate_template",
        _mock_invoke,
    )

    result = elasticsearch_tools.es_compare_time_windows(
        elasticsearch_tools.EsCompareTimeWindowsInput(
            current_start=_START,
            current_end=_END,
            baseline_start=_BASELINE_START,
            baseline_end=_BASELINE_END,
            template="traffic",
        )
    )

    assert result["ok"] is True
    assert result["tool"] == "es_compare_time_windows"
    assert result["comparison"]["current_total"] == 40
    assert result["comparison"]["baseline_total"] == 20
    assert result["comparison"]["delta"] == 20
    assert result["comparison"]["change_percent"] == 100.0
    _assert_no_placeholder(result)


def test_es_detect_traffic_peak_oversized_window_structured_error() -> None:
    wide_end = _START + timedelta(hours=25)

    result = elasticsearch_tools.es_detect_traffic_peak(
        elasticsearch_tools.EsDetectTrafficPeakInput(start_time=_START, end_time=wide_end)
    )

    assert result["ok"] is False
    assert result["tool"] == "es_detect_traffic_peak"
    assert "24" in result["error"]
    _assert_no_placeholder(result)


# ---------------------------------------------------------------------------
# 辅助工具 14 / 15 / 16
# ---------------------------------------------------------------------------


def test_kibana_generate_link_offline_url() -> None:
    result = kibana_tools.kibana_generate_link(
        kibana_tools.KibanaGenerateLinkInput(
            index_pattern="app-logs-*",
            start_time=_START,
            end_time=_END,
            query="payment timeout",
        )
    )

    assert result["ok"] is True
    assert result["tool"] == "kibana_generate_link"
    assert result["url"].startswith("http")
    assert "/app/discover" in result["url"]
    assert "app-logs-*" in result["url"]
    _assert_no_placeholder(result)


def test_report_list_recent_mock_service(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.tools.report_tools.list_recent_reports",
        lambda limit, report_type=None: {
            "ok": True,
            "items": [{"report_id": "rpt-001", "title": "周报"}],
            "total": 1,
            "limit": limit,
        },
    )

    result = report_tools.report_list_recent(
        report_tools.ReportListRecentInput(limit=5, report_type="periodic")
    )

    assert result["ok"] is True
    assert result["tool"] == "report_list_recent"
    assert result["items"][0]["report_id"] == "rpt-001"
    _assert_no_placeholder(result)


def test_alert_list_active_mock_service(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.tools.alert_tools.alert_service.list_active_alerts",
        lambda limit: {
            "ok": True,
            "items": [{"alert_id": "alert-001", "severity": "high"}],
            "total": 1,
            "limit": limit,
        },
    )

    result = alert_tools.alert_list_active(alert_tools.AlertListActiveInput(limit=10))

    assert result["ok"] is True
    assert result["tool"] == "alert_list_active"
    assert result["items"][0]["alert_id"] == "alert-001"
    _assert_no_placeholder(result)


# ---------------------------------------------------------------------------
# 注册中心 16 工具 + 读写分离
# ---------------------------------------------------------------------------


def test_list_registered_tool_names_sixteen() -> None:
    names = list_registered_tool_names()

    assert len(names) == 16
    assert names[0] == "es_search_logs"
    assert names[-1] == "alert_list_active"
    assert "es_get_business_funnel" in names
    assert "kibana_generate_link" in names


def test_get_langchain_tools_read_write_separation() -> None:
    read_tools = get_langchain_tools()
    read_names = {tool.name for tool in read_tools}
    all_tools = get_langchain_tools(include_write_tools=True)
    all_names = {tool.name for tool in all_tools}

    assert len(read_tools) == 14
    assert len(all_tools) == 16
    assert _WRITE_TOOL_NAMES.isdisjoint(read_names)
    assert _WRITE_TOOL_NAMES.issubset(all_names)
    assert _NEW_READ_TOOL_NAMES.issubset(read_names)


# ---------------------------------------------------------------------------
# MCP create_mcp_server + run_mcp_server --list
# ---------------------------------------------------------------------------


def test_create_mcp_server_fastmcp_missing_degraded(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def _blocking_fastmcp(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "fastmcp" or name.startswith("fastmcp."):
            raise ImportError("fastmcp 未安装")
        return real_import(name, *args, **kwargs)

    monkeypatch.delitem(sys.modules, "fastmcp", raising=False)
    monkeypatch.setattr(builtins, "__import__", _blocking_fastmcp)

    result = create_mcp_server()

    assert isinstance(result, dict)
    assert result["ok"] is False
    assert result["error"] == "fastmcp 未安装"


def test_create_mcp_server_fake_fastmcp_registers_read_only_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registered: list[str] = []

    class FakeFastMCP:
        def __init__(self, name: str) -> None:
            self.name = name

        def add_tool(self, fn: Any) -> None:
            registered.append(fn.__name__)

    fake_module = types.ModuleType("fastmcp")
    fake_module.FastMCP = FakeFastMCP
    monkeypatch.setitem(sys.modules, "fastmcp", fake_module)

    server = create_mcp_server()

    assert isinstance(server, FakeFastMCP)
    assert "analysis_write_report" not in registered
    assert "alert_write_event" not in registered
    assert "es_search_logs" in registered
    assert "kibana_generate_link" in registered
    assert len(registered) == 14


def test_run_mcp_server_list_prints_read_tools(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "app.tasks.run_mcp_server.create_mcp_server",
        lambda: {"ok": False, "error": "fastmcp 未安装"},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_mcp_server", "--list"],
    )

    from app.tasks.run_mcp_server import main

    main()
    captured = capsys.readouterr().out

    assert "读类工具列表" in captured
    assert "es_search_logs" in captured
    assert "kibana_generate_link" in captured
    assert "analysis_write_report" not in captured
    assert "alert_write_event" not in captured
    assert "共 14 个" in captured
