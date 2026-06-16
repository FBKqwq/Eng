"""M1-08：index_service 单元测试（mock ES）+ 可选集成测试。"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from elasticsearch import ConnectionError

from app.services.elasticsearch.index_service import (
    create_analysis_indices,
    create_component_templates,
    create_index_templates,
    init_all_indices,
    verify_templates,
)

_PATCH_GET_ES_CLIENT = "app.services.elasticsearch.index_service.get_es_client"


def _assert_no_placeholder(obj: Any) -> None:
    """递归检查返回值不含 placeholder 键。"""
    if isinstance(obj, dict):
        assert "placeholder" not in obj
        for value in obj.values():
            _assert_no_placeholder(value)
    elif isinstance(obj, list):
        for item in obj:
            _assert_no_placeholder(item)


def test_init_all_indices_es_unavailable() -> None:
    """ES 连接失败时 init_all_indices 返回 ok=False。"""
    mock_client = MagicMock()
    mock_client.cluster.put_component_template.side_effect = ConnectionError("N/A")
    with patch(_PATCH_GET_ES_CLIENT, return_value=mock_client):
        result = init_all_indices()
    assert result["ok"] is False
    assert "error" in result
    assert "steps" in result
    assert result["steps"][0]["ok"] is False
    _assert_no_placeholder(result)


def test_verify_templates_missing() -> None:
    """模板不存在时 verify_templates 报告 missing 非空。"""
    mock_client = MagicMock()
    mock_client.cluster.get_component_template.side_effect = Exception("not found")
    mock_client.indices.get_index_template.side_effect = Exception("not found")
    with patch(_PATCH_GET_ES_CLIENT, return_value=mock_client):
        result = verify_templates()
    assert result["ok"] is False
    assert len(result["missing"]) > 0
    assert any(item.startswith("component:") for item in result["missing"])
    assert any(item.startswith("index:") for item in result["missing"])
    _assert_no_placeholder(result)


def test_create_component_templates_success() -> None:
    """mock ES 成功时 create_component_templates 返回 ok=True。"""
    mock_client = MagicMock()
    with patch(_PATCH_GET_ES_CLIENT, return_value=mock_client):
        result = create_component_templates()
    assert result["ok"] is True
    assert result["count"] == 8
    assert len(result["templates"]) == 8
    assert mock_client.cluster.put_component_template.call_count == 8
    _assert_no_placeholder(result)


def test_verify_templates_all_present() -> None:
    """全部模板存在时 verify_templates 返回 ok=True、missing 为空。"""
    mock_client = MagicMock()
    with patch(_PATCH_GET_ES_CLIENT, return_value=mock_client):
        result = verify_templates()
    assert result["ok"] is True
    assert result["missing"] == []
    _assert_no_placeholder(result)


def test_no_placeholder_in_response() -> None:
    """各公开函数返回值均无 placeholder 键。"""
    mock_client = MagicMock()
    with patch(_PATCH_GET_ES_CLIENT, return_value=mock_client):
        for fn in (
            create_component_templates,
            create_index_templates,
            create_analysis_indices,
            init_all_indices,
            verify_templates,
        ):
            _assert_no_placeholder(fn())


def test_verify_templates_client_unreachable() -> None:
    """get_es_client 抛错时 verify_templates 返回 ok=False 并列出全部 missing。"""
    with patch(_PATCH_GET_ES_CLIENT, side_effect=ConnectionError("refused")):
        result = verify_templates()
    assert result["ok"] is False
    assert len(result["missing"]) > 0
    assert "error" in result
    _assert_no_placeholder(result)


@pytest.mark.integration
def test_init_all_indices_success_integration() -> None:
    """ES 在线时 init_all_indices 完整成功（可选集成）。"""
    try:
        from app.services.elasticsearch.client import get_es_client

        client = get_es_client()
        if not client.ping():
            pytest.skip("Elasticsearch 未在线")
    except Exception as exc:
        pytest.skip(f"Elasticsearch 不可达: {exc}")

    result = init_all_indices()
    assert result["ok"] is True
    assert len(result["steps"]) == 3
    assert all(step["ok"] for step in result["steps"])
    _assert_no_placeholder(result)
