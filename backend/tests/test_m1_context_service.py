"""M1-10：context_service 单元测试（mock ES，离线可跑）。"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 使 `pytest tests/...` 在 backend 根目录下可直接发现 app 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.elasticsearch.context_service import (
    get_service_window,
    get_similar_errors,
    get_trace_context,
    get_user_recent_actions,
)

_START = datetime(2026, 6, 16, 10, 0, 0)
_END = datetime(2026, 6, 16, 11, 0, 0)


def _make_es_mock(search_return: dict | None = None, *, side_effect: Exception | None = None) -> MagicMock:
    """构造 get_es_client 返回的链式 mock：client.options().search()。"""
    client = MagicMock()
    options_client = MagicMock()
    client.options.return_value = options_client
    if side_effect is not None:
        options_client.search.side_effect = side_effect
    else:
        options_client.search.return_value = search_return or {}
    return client


def _sample_hit(log_id: str = "log-1", level: str = "ERROR") -> dict:
    return {
        "_id": log_id,
        "_source": {
            "log_id": log_id,
            "log_level": level,
            "service_name": "order-service",
            "message": "sample",
            "timestamp": "2026-06-16T10:30:00",
        },
    }


@patch("app.services.elasticsearch.context_service.get_es_client")
def test_get_trace_context_empty(mock_get_es: MagicMock) -> None:
    """ES 返回空 hits 时 total=0、available=True。"""
    mock_get_es.return_value = _make_es_mock(
        {
            "took": 3,
            "hits": {"total": {"value": 0}, "hits": []},
        }
    )

    result = get_trace_context("trace-empty-001")

    assert result["available"] is True
    assert result["error"] is None
    assert result["total"] == 0
    assert result["items"] == []
    assert result["trace_id"] == "trace-empty-001"


@patch("app.services.elasticsearch.context_service.get_es_client")
def test_get_trace_context_es_offline(mock_get_es: MagicMock) -> None:
    """ES 连接失败时 available=False 并携带错误信息。"""
    mock_get_es.return_value = _make_es_mock(side_effect=ConnectionError("ES offline"))

    result = get_trace_context("trace-offline-001")

    assert result["available"] is False
    assert result["error"] is not None
    assert "ES offline" in result["error"]
    assert result["total"] == 0
    assert result["items"] == []


@patch("app.services.elasticsearch.context_service.get_es_client")
def test_get_service_window_level_distribution(mock_get_es: MagicMock) -> None:
    """服务窗口查询应解析 level_distribution 聚合。"""
    mock_get_es.return_value = _make_es_mock(
        {
            "took": 12,
            "hits": {
                "total": {"value": 7},
                "hits": [_sample_hit("log-err", "ERROR")],
            },
            "aggregations": {
                "level_distribution": {
                    "buckets": [
                        {"key": "ERROR", "doc_count": 2},
                        {"key": "INFO", "doc_count": 5},
                    ]
                }
            },
        }
    )

    result = get_service_window("order-service", _START, _END)

    assert result["available"] is True
    assert result["level_distribution"] == {"ERROR": 2, "INFO": 5}
    assert result["service"] == "order-service"
    assert len(result["items"]) == 1


@patch("app.services.elasticsearch.context_service.get_es_client")
def test_get_similar_errors_total(mock_get_es: MagicMock) -> None:
    """同类错误查询应返回 mock 命中的 total。"""
    mock_get_es.return_value = _make_es_mock(
        {
            "took": 8,
            "hits": {"total": {"value": 5}, "hits": []},
            "aggregations": {
                "by_service": {
                    "buckets": [{"key": "payment-service", "doc_count": 5}]
                },
                "time_histogram": {"buckets": []},
            },
        }
    )

    result = get_similar_errors("PAY_TIMEOUT", _START, _END)

    assert result["available"] is True
    assert result["total"] == 5
    assert result["error_code"] == "PAY_TIMEOUT"
    assert result["by_service"][0]["key"] == "payment-service"
    assert result["by_service"][0]["count"] == 5


@patch("app.services.elasticsearch.context_service.get_es_client")
def test_limit_capped_at_50(mock_get_es: MagicMock) -> None:
    """传入 limit=200 时 ES search 的 size 应被限制为 50。"""
    mock_get_es.return_value = _make_es_mock(
        {"took": 1, "hits": {"total": {"value": 0}, "hits": []}}
    )

    get_trace_context("trace-limit", limit=200)

    options_client = mock_get_es.return_value.options.return_value
    _, kwargs = options_client.search.call_args
    assert kwargs["size"] == 50


@patch("app.services.elasticsearch.context_service.get_es_client")
def test_get_trace_context_empty_trace_id_skips_es(mock_get_es: MagicMock) -> None:
    """空 trace_id 直接返回校验错误，不调用 ES。"""
    result = get_trace_context("   ")

    assert result["available"] is False
    assert "trace_id" in result["error"]
    mock_get_es.assert_not_called()


@patch("app.services.elasticsearch.context_service.get_es_client")
def test_get_service_window_invalid_time_window(mock_get_es: MagicMock) -> None:
    """end < start 时返回窗口校验错误，不调用 ES。"""
    result = get_service_window("order-service", _END, _START)

    assert result["available"] is False
    assert "end" in result["error"]
    assert result["level_distribution"] == {}
    mock_get_es.assert_not_called()


@pytest.mark.skip(reason="需要在线 Elasticsearch，离线环境跳过")
@patch("app.services.elasticsearch.context_service.get_es_client")
def test_get_user_recent_actions(mock_get_es: MagicMock) -> None:
    """integration：用户近期行为查询（需 ES 在线时可手动启用）。"""
    mock_get_es.return_value = _make_es_mock(
        {
            "took": 5,
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_id": "u1",
                        "_source": {
                            "log_id": "u1",
                            "user_id": "user-42",
                            "event_type": "page_view",
                            "timestamp": "2026-06-16T10:15:00",
                        },
                    }
                ],
            },
        }
    )

    result = get_user_recent_actions("user-42", _START, _END)

    assert result["available"] is True
    assert result["total"] == 1
    assert result["user_id"] == "user-42"
