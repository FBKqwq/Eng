"""M2-07：tools 层单元测试（mock ES/Kafka/底层 service，离线可跑）。"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas.log import TimeInterval
from app.schemas.system import DockerStatusResponse, ElasticsearchHealthSnapshot, KafkaStatusSnapshot, KafkaTopicSnapshot
from app.services.tools import alert_tools, elasticsearch_tools, report_tools, rule_tools, system_tools
from app.services.tools.registry import get_langchain_tools, list_registered_tool_names

_START = datetime(2026, 6, 16, 10, 0, 0)
_END = datetime(2026, 6, 16, 11, 0, 0)

_ES_SEARCH_OK = {
    "available": True,
    "error": None,
    "items": [{"log_id": "log-1", "message": "ok"}],
    "total": 1,
    "page": 1,
    "page_size": 50,
    "has_more": False,
    "took_ms": 5,
}

_AGG_OK = {
    "available": True,
    "error": None,
    "buckets": [{"key": "order-service", "count": 3}],
    "total": 3,
}

_CONTEXT_OK = {
    "available": True,
    "error": None,
    "total": 1,
    "items": [{"log_id": "ctx-1"}],
}


def _assert_no_placeholder(result: dict) -> None:
    assert "placeholder" not in result


def _es_snapshot(*, available: bool = True) -> ElasticsearchHealthSnapshot:
    return ElasticsearchHealthSnapshot(
        hosts=["http://localhost:9200"],
        index_pattern="app-logs-*",
        available=available,
        cluster_status="green" if available else "unknown",
    )


def _kafka_snapshot(*, available: bool = True) -> KafkaStatusSnapshot:
    return KafkaStatusSnapshot(
        bootstrap_servers=["localhost:9092"],
        topic="app-logs",
        available=available,
        configured_topic=KafkaTopicSnapshot(name="app-logs", exists=True, partitions=1, replication_factor=1),
    )


def _docker_snapshot(*, available: bool = True) -> DockerStatusResponse:
    return DockerStatusResponse(project="elk", available=available, containers={})


@patch("app.services.tools.elasticsearch_tools.log_query_service.search_logs")
def test_es_search_logs_ok(mock_search: MagicMock) -> None:
    mock_search.return_value = _ES_SEARCH_OK

    result = elasticsearch_tools.es_search_logs(
        elasticsearch_tools.EsSearchLogsInput(keyword="timeout", limit=10)
    )

    assert result["ok"] is True
    assert result["tool"] == "es_search_logs"
    assert result["total"] == 1
    _assert_no_placeholder(result)
    mock_search.assert_called_once()


def test_es_search_logs_invalid_time_window() -> None:
    result = elasticsearch_tools.es_search_logs(
        elasticsearch_tools.EsSearchLogsInput(
            start_time=_END,
            end_time=_START,
        )
    )

    assert result["ok"] is False
    assert result["tool"] == "es_search_logs"
    assert "end_time" in result["error"]


@patch("app.services.tools.elasticsearch_tools.log_query_service.search_logs")
def test_es_search_logs_service_raises(mock_search: MagicMock) -> None:
    mock_search.side_effect = RuntimeError("ES connection refused")

    result = elasticsearch_tools.es_search_logs(elasticsearch_tools.EsSearchLogsInput())

    assert result["ok"] is False
    assert result["tool"] == "es_search_logs"
    assert "ES connection refused" in result["error"]


@pytest.mark.parametrize(
    "template",
    ["traffic", "errors", "latency", "behavior_funnel", "security", "infra_health"],
)
def test_es_aggregate_metrics_templates(template: str) -> None:
    mock_handler = MagicMock(return_value=_AGG_OK)
    with patch.dict(
        elasticsearch_tools._AGGREGATE_DISPATCH,
        {template: mock_handler},
    ):
        result = elasticsearch_tools.es_aggregate_metrics(
            elasticsearch_tools.EsAggregateMetricsInput(
                template=template,
                start_time=_START,
                end_time=_END,
                interval=TimeInterval.minute,
            )
        )

    assert result["ok"] is True
    assert result["tool"] == "es_aggregate_metrics"
    _assert_no_placeholder(result)
    mock_handler.assert_called_once()


@patch("app.services.tools.elasticsearch_tools.context_service.get_trace_context")
def test_es_get_trace_context(mock_get_trace: MagicMock) -> None:
    mock_get_trace.return_value = {**_CONTEXT_OK, "trace_id": "trace-abc"}

    result = elasticsearch_tools.es_get_trace_context("trace-abc", limit=20)

    assert result["ok"] is True
    assert result["tool"] == "es_get_trace_context"
    assert result["trace_id"] == "trace-abc"
    _assert_no_placeholder(result)


@patch("app.services.tools.elasticsearch_tools.context_service.get_service_window")
def test_es_get_service_window(mock_get_window: MagicMock) -> None:
    mock_get_window.return_value = {**_CONTEXT_OK, "service": "order-service"}

    result = elasticsearch_tools.es_get_service_window("order-service", _START, _END)

    assert result["ok"] is True
    assert result["tool"] == "es_get_service_window"
    assert result["service"] == "order-service"
    _assert_no_placeholder(result)


@patch("app.services.tools.elasticsearch_tools.context_service.get_similar_errors")
def test_es_get_similar_errors(mock_get_similar: MagicMock) -> None:
    mock_get_similar.return_value = {**_CONTEXT_OK, "error_code": "E500"}

    result = elasticsearch_tools.es_get_similar_errors("E500", _START, _END)

    assert result["ok"] is True
    assert result["tool"] == "es_get_similar_errors"
    assert result["error_code"] == "E500"
    _assert_no_placeholder(result)


@patch("app.services.tools.system_tools.get_docker_status")
@patch("app.services.tools.system_tools.get_kafka_status_snapshot")
@patch("app.services.tools.system_tools.get_elasticsearch_health_snapshot")
def test_system_health_check_sections(
    mock_es: MagicMock,
    mock_kafka: MagicMock,
    mock_docker: MagicMock,
) -> None:
    mock_es.return_value = _es_snapshot()
    mock_kafka.return_value = _kafka_snapshot()
    mock_docker.return_value = _docker_snapshot()

    result = system_tools.system_health_check()

    assert result["tool"] == "system_health_check"
    assert result["ok"] is True
    assert "elasticsearch" in result
    assert "kafka" in result
    assert "docker" in result
    assert result["elasticsearch"]["available"] is True
    assert result["kafka"]["available"] is True
    assert result["docker"]["available"] is True
    _assert_no_placeholder(result)


@patch("app.services.tools.rule_tools.match_log")
def test_rule_match_log_structured(mock_match: MagicMock) -> None:
    mock_match.return_value = {
        "ok": True,
        "matched": True,
        "rule_id": "R001",
        "rule_name": "支付超时",
        "severity": "high",
        "trigger_subgraph": False,
        "log_event_id": "log-99",
    }

    result = rule_tools.rule_match_log(
        rule_tools.RuleMatchLogInput(log_event={"log_id": "log-99", "message": "pay timeout"})
    )

    assert result["tool"] == "rule_match_log"
    assert result["matched"] is True
    assert result["rule_id"] == "R001"
    _assert_no_placeholder(result)


@patch("app.services.tools.report_tools.write_report")
def test_analysis_write_report_structured(mock_write: MagicMock) -> None:
    mock_write.return_value = {
        "ok": True,
        "report_id": "rep-001",
        "message": "已写入",
    }

    result = report_tools.analysis_write_report(
        report_tools.WriteReportInput(report={"title": "诊断报告", "summary": "ok"})
    )

    assert result["tool"] == "analysis_write_report"
    assert result["ok"] is True
    assert result["report_id"] == "rep-001"
    _assert_no_placeholder(result)


@patch("app.services.tools.alert_tools.alert_service.write_alert")
def test_alert_write_event_structured(mock_write: MagicMock) -> None:
    mock_write.return_value = {
        "ok": True,
        "alert_id": "alert-001",
    }

    result = alert_tools.alert_write_event(
        alert_tools.WriteAlertInput(alert={"alert_type": "error_spike", "affected_service": "pay"})
    )

    assert result["tool"] == "alert_write_event"
    assert result["ok"] is True
    assert result["alert_id"] == "alert-001"
    _assert_no_placeholder(result)


@patch("app.services.tools.alert_tools.dedup.check_duplicate")
def test_alert_check_duplicate_structured(mock_check: MagicMock) -> None:
    mock_check.return_value = {
        "ok": True,
        "is_duplicate": False,
        "existing_alert_id": None,
        "bucket_minutes": 10,
    }

    result = alert_tools.alert_check_duplicate(
        alert_tools.CheckDuplicateInput(
            alert_candidate={"alert_type": "error_spike", "affected_service": "pay"},
            bucket_minutes=10,
        )
    )

    assert result["tool"] == "alert_check_duplicate"
    assert result["ok"] is True
    assert result["is_duplicate"] is False
    _assert_no_placeholder(result)


def test_registry_default_read_tools_count() -> None:
    tools = get_langchain_tools()
    names = [tool.name for tool in tools]

    # M2 第一阶段 8 个读类 + M7 第二阶段 6 个读类 = 14 个读类工具
    assert len(tools) == 14
    assert "analysis_write_report" not in names
    assert "alert_write_event" not in names
    assert "es_search_logs" in names
    assert "rule_match_log" in names


def test_registry_include_write_tools_count() -> None:
    tools = get_langchain_tools(include_write_tools=True)
    names = [tool.name for tool in tools]

    # 14 个读类 + 2 个写类（analysis_write_report / alert_write_event）= 16
    assert len(tools) == 16
    assert "analysis_write_report" in names
    assert "alert_write_event" in names


def test_list_registered_tool_names_stable_order() -> None:
    names = list_registered_tool_names()

    assert len(names) == 16
    assert names[0] == "es_search_logs"
    assert names[-1] == "alert_list_active"
    assert names == [
        "es_search_logs",
        "es_aggregate_metrics",
        "es_get_trace_context",
        "es_get_service_window",
        "es_get_similar_errors",
        "analysis_write_report",
        "alert_write_event",
        "alert_check_duplicate",
        "system_health_check",
        "rule_match_log",
        "es_get_business_funnel",
        "es_detect_traffic_peak",
        "es_compare_time_windows",
        "kibana_generate_link",
        "report_list_recent",
        "alert_list_active",
    ]


@patch("app.services.tools.elasticsearch_tools.log_query_service.search_logs")
def test_structured_tool_invoke_es_search_logs(mock_search: MagicMock) -> None:
    mock_search.return_value = _ES_SEARCH_OK

    tool = next(t for t in get_langchain_tools() if t.name == "es_search_logs")
    result = tool.invoke({"keyword": "payment", "limit": 5})

    assert result["ok"] is True
    assert result["tool"] == "es_search_logs"
    assert result["total"] == 1
    _assert_no_placeholder(result)
