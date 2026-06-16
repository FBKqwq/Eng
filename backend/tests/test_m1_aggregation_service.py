"""M1-09：aggregation_service 单元测试（mock ES）+ 可选集成测试。

集成测试数据准备（ES 在线且有索引数据时）：
    python -m app.tasks.run_log_producer --count 100
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.log import AggregateField, LogAggregateRequest, LogType
from app.services.elasticsearch.aggregation_service import (
    MAX_TOP_N,
    aggregate,
    aggregate_traffic,
)

_PATCH_GET_ES_CLIENT = "app.services.elasticsearch.aggregation_service.get_es_client"


def _recent_window(*, hours: float = 1.0) -> tuple[datetime, datetime]:
    end = datetime.now(timezone.utc).replace(tzinfo=None)
    start = end - timedelta(hours=hours)
    return start, end


def _mock_es_search_response(aggs: dict[str, Any] | None = None) -> MagicMock:
    mock_client = MagicMock()
    mock_client.options.return_value = mock_client
    mock_client.search.return_value = {
        "aggregations": aggs or {"by_group": {"buckets": []}},
        "took": 12,
    }
    return mock_client


@patch(_PATCH_GET_ES_CLIENT)
def test_aggregate_invalid_group_by_does_not_call_es(mock_get_client: MagicMock) -> None:
    """非法 group_by 校验失败时不触发 client.search（call_count=0）。"""
    start, end = _recent_window()
    request = LogAggregateRequest(
        start_time=start,
        end_time=end,
        log_types=[LogType.behavior],
        group_by=AggregateField.error_code,
    )

    result = aggregate(request)

    assert result["available"] is False
    assert result["buckets"] == []
    assert result["error"] is not None
    mock_get_client.assert_not_called()


@patch(_PATCH_GET_ES_CLIENT)
def test_aggregate_top_n_capped_at_50(mock_get_client: MagicMock) -> None:
    """top_n 超过上限时在 DSL terms.size 中截断为 50。"""
    mock_get_client.return_value = _mock_es_search_response()
    start, end = _recent_window()
    request = LogAggregateRequest(
        start_time=start,
        end_time=end,
        log_types=[LogType.application],
        group_by=AggregateField.error_code,
        top_n=200,
    )

    result = aggregate(request)

    assert result["available"] is True
    search_kwargs = mock_get_client.return_value.search.call_args.kwargs
    assert search_kwargs["aggs"]["by_group"]["terms"]["size"] == MAX_TOP_N
    assert MAX_TOP_N == 50


@patch(_PATCH_GET_ES_CLIENT)
def test_aggregate_es_offline(mock_get_client: MagicMock) -> None:
    """ES 离线时 aggregate_traffic 返回 available=False 且含错误信息。"""
    mock_get_client.side_effect = Exception("connection refused")
    start, end = _recent_window()

    result = aggregate_traffic(start_time=start, end_time=end)

    assert result["available"] is False
    assert result["buckets"] == []
    assert "connection refused" in (result["error"] or "")


@patch(_PATCH_GET_ES_CLIENT)
def test_aggregate_invalid_time_window_does_not_call_es(mock_get_client: MagicMock) -> None:
    """时间窗非法时不调用 ES。"""
    start, end = _recent_window()
    request = LogAggregateRequest(
        start_time=end,
        end_time=start,
        log_types=[LogType.application],
        group_by=AggregateField.service_name,
    )

    result = aggregate(request)

    assert result["available"] is False
    assert "end_time" in (result["error"] or "")
    mock_get_client.assert_not_called()


@patch(_PATCH_GET_ES_CLIENT)
def test_aggregate_traffic_top_n_capped_in_dsl(mock_get_client: MagicMock) -> None:
    """aggregate_traffic 的 by_service terms.size 受 top_n 上限约束。"""
    mock_get_client.return_value = _mock_es_search_response(
        {
            "traffic_over_time": {"buckets": [{"key": "2026-01-01", "doc_count": 3}]},
            "by_service": {"buckets": []},
        }
    )
    start, end = _recent_window()

    result = aggregate_traffic(start_time=start, end_time=end, top_n=999)

    assert result["available"] is True
    search_kwargs = mock_get_client.return_value.search.call_args.kwargs
    assert search_kwargs["aggs"]["by_service"]["terms"]["size"] == MAX_TOP_N


@pytest.mark.integration
def test_aggregate_traffic_integration_buckets_non_empty() -> None:
    """ES 在线且有日志数据时 aggregate_traffic 返回非空 buckets。

    数据准备：python -m app.tasks.run_log_producer --count 100
    """
    try:
        from app.services.elasticsearch.client import get_es_client

        client = get_es_client()
        if not client.ping():
            pytest.skip("Elasticsearch 未在线")
    except Exception as exc:
        pytest.skip(f"Elasticsearch 不可达: {exc}")

    start, end = _recent_window(hours=24)
    result = aggregate_traffic(start_time=start, end_time=end, top_n=10)

    if not result["available"]:
        pytest.skip(f"ES 聚合不可用: {result.get('error')}")

    assert isinstance(result["buckets"], list)
    assert len(result["buckets"]) > 0
