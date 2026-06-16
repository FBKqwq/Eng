"""M1-07：field_catalog 单元测试（纯单元，不依赖 ES）。"""

from app.services.elasticsearch.field_catalog import (
    FIELD_CATALOG,
    get_catalog_for_log_type,
    list_registered_log_types,
    resolve_index_pattern,
    validate_aggregate_field,
    validate_aggregate_request,
)

_EXPECTED_LOG_TYPES = {
    "behavior",
    "application",
    "web_server",
    "performance",
    "security",
    "infrastructure",
    "audit",
}

_EXPECTED_FUNNEL_STEPS = [
    "page_view",
    "product_click",
    "add_to_cart",
    "checkout_click",
    "pay_button_click",
]


def test_list_registered_log_types() -> None:
    """返回固定 7 类 log_type。"""
    types = list_registered_log_types()
    assert len(types) == 7
    assert set(types) == _EXPECTED_LOG_TYPES


def test_field_catalog_has_seven_entries() -> None:
    """FIELD_CATALOG 与注册类型一一对应。"""
    assert len(FIELD_CATALOG) == 7
    assert set(FIELD_CATALOG.keys()) == _EXPECTED_LOG_TYPES


def test_behavior_funnel_steps() -> None:
    """behavior 漏斗五步顺序固定。"""
    catalog = get_catalog_for_log_type("behavior")
    assert catalog["funnel_steps"] == _EXPECTED_FUNNEL_STEPS


def test_validate_aggregate_field_rejects_text() -> None:
    """message 在 filter 白名单但不在 terms 白名单，terms 聚合应拒绝。"""
    assert validate_aggregate_field("behavior", "message", "filter") is True
    assert validate_aggregate_field("behavior", "message", "terms") is False


def test_validate_aggregate_field_accepts_keyword() -> None:
    """application.error_code 在 terms 白名单内，应允许聚合。"""
    assert validate_aggregate_field("application", "error_code", "terms") is True


def test_validate_aggregate_field_rejects_unknown_kind() -> None:
    """非法 field_kind 一律拒绝。"""
    assert validate_aggregate_field("application", "error_code", "text") is False


def test_resolve_index_pattern_single() -> None:
    """单类型索引 pattern 不含逗号。"""
    pattern = resolve_index_pattern(["application"])
    assert pattern == "app-logs-application-*"
    assert "," not in pattern


def test_resolve_index_pattern_multi() -> None:
    """多类型索引 pattern 以逗号拼接；web_server 保留下划线与 Logstash / index_service 一致。"""
    pattern = resolve_index_pattern(["application", "web_server"])
    assert "," in pattern
    assert pattern == "app-logs-application-*,app-logs-web_server-*"


def test_resolve_index_pattern_web_server() -> None:
    """web_server 单类型索引 pattern 使用下划线，非连字符。"""
    pattern = resolve_index_pattern(["web_server"])
    assert pattern == "app-logs-web_server-*"


def test_validate_aggregate_request_invalid_group_by() -> None:
    """group_by 不在 terms 白名单时 ok=False 并返回错误列表。"""
    result = validate_aggregate_request(["behavior"], "message")
    assert result["ok"] is False
    assert isinstance(result["errors"], list)
    assert len(result["errors"]) > 0
    assert any("group_by" in err for err in result["errors"])


def test_validate_aggregate_request_accepts_valid_group_by() -> None:
    """合法 group_by 应通过校验。"""
    result = validate_aggregate_request(["application"], "error_code")
    assert result["ok"] is True
    assert result["errors"] == []


def test_unknown_log_type_catalog() -> None:
    """未知 log_type 返回 ok=False 结构，不含 catalog 占位键。"""
    catalog = get_catalog_for_log_type("not_a_real_log_type")
    assert catalog["ok"] is False
    assert "message" in catalog
    assert "filter_fields" not in catalog
    assert "terms_fields" not in catalog
    assert "metric_fields" not in catalog
