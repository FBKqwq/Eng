"""M3-08：LangChain 层单元测试（全程 mock LLM，不联网、不依赖 ES）。"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.langchain import evidence_builder, llm_manager, prompts, report_chain
from app.services.langchain.chain_schemas import DiagnosisChainOutput, ReportChainOutput
from app.services.langchain.diagnosis_chain import generate_event_report, infer_root_cause
from app.services.langchain.output_parsers import parse_with_retry

# ---------------------------------------------------------------------------
# 测试夹具与辅助
# ---------------------------------------------------------------------------

_REPORT_LLM_DATA = {
    "report_type": "periodic",
    "title": "测试周期报告",
    "risk_level": "medium",
    "summary": "LLM 生成的摘要",
    "key_findings": ["发现 A"],
    "recommendations": ["建议 B"],
}

_DIAGNOSIS_LLM_DATA = {
    "root_cause": "支付服务超时导致失败",
    "confidence": 0.85,
    "severity": "high",
    "affected_services": ["payment-service"],
    "evidence_refs": ["PAY_TIMEOUT x5"],
    "action_suggestions": ["检查下游依赖"],
}

_SAMPLE_EVIDENCE_PACKAGE = {
    "summary": {
        "total_logs": 20,
        "error_count": 5,
        "warn_count": 2,
        "top_services": ["payment-service", "order-service"],
        "top_error_codes": ["PAY_FAIL"],
    },
    "grouped": {
        "by_service": {"payment-service": 12, "order-service": 8},
        "by_error_code": {"PAY_FAIL": 5},
        "by_log_level": {"ERROR": 5, "WARNING": 2, "INFO": 13},
    },
    "samples": [
        {
            "log_level": "ERROR",
            "service_name": "payment-service",
            "error_code": "PAY_FAIL",
            "message": "支付失败",
        }
    ],
    "metrics": {"error_rate": 0.25, "request_total": 1000},
}


def _assert_no_placeholder(result: dict[str, Any]) -> None:
    """递归检查产出 dict 不含 placeholder 键。"""
    assert "placeholder" not in result
    for value in result.values():
        if isinstance(value, dict):
            _assert_no_placeholder(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _assert_no_placeholder(item)


def _make_log(
    level: str,
    *,
    service: str = "test-service",
    error_code: str | None = None,
    message: str = "测试日志",
    log_id: str | None = None,
) -> dict[str, Any]:
    return {
        "log_id": log_id or f"log-{service}-{level}",
        "log_level": level,
        "service_name": service,
        "message": message,
        "error_code": error_code,
        "timestamp": "2026-06-22T10:00:00",
    }


# ---------------------------------------------------------------------------
# llm_manager
# ---------------------------------------------------------------------------


def test_llm_manager_unavailable_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """无 API Key 时 is_llm_available 返回 False。"""
    monkeypatch.setattr(llm_manager.settings, "llm_api_key", "")
    assert llm_manager.is_llm_available() is False


def test_invoke_structured_degraded_when_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """LLM 不可用时 invoke_structured 返回降级结构。"""
    monkeypatch.setattr(llm_manager, "is_llm_available", lambda: False)

    result = llm_manager.invoke_structured("report", "prompt", ReportChainOutput)

    assert result == {"ok": False, "available": False, "reason": "llm_unavailable"}


# ---------------------------------------------------------------------------
# prompts
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    ["report", "diagnosis", "evidence_summary", "alert"],
)
def test_get_prompt_non_placeholder_templates(name: str) -> None:
    """四类已实现 Prompt 返回非占位模板。"""
    template = prompts.get_prompt(name)
    assert template
    assert "placeholder" not in template.lower()
    assert len(template) > 50


def test_get_prompt_relation_is_production_template() -> None:
    """relation 模板已在 M7 投产，不再是占位说明。"""
    template = prompts.get_prompt("relation")
    assert template
    assert not template.startswith("[M7")
    assert "placeholder" not in template.lower()
    assert len(template) > 50


def test_get_prompt_unknown_returns_empty() -> None:
    """未知名称返回空字符串。"""
    assert prompts.get_prompt("nonexistent") == ""


# ---------------------------------------------------------------------------
# output_parsers
# ---------------------------------------------------------------------------


def test_parse_with_retry_valid_json() -> None:
    """合法 JSON 直接解析成功。"""
    raw = (
        '{"report_type":"periodic","title":"t","risk_level":"low",'
        '"summary":"s","key_findings":["f1"],"recommendations":["r1"]}'
    )
    result = parse_with_retry(raw, ReportChainOutput)

    assert result["ok"] is True
    assert result["data"]["title"] == "t"
    assert result["data"]["risk_level"] == "low"


def test_parse_with_retry_code_block_wrapped() -> None:
    """Markdown 代码块包裹的 JSON 可解析。"""
    raw = """```json
{
  "root_cause": "数据库连接池耗尽",
  "confidence": 0.7,
  "severity": "medium",
  "affected_services": ["db-proxy"],
  "evidence_refs": ["DB_POOL x3"],
  "action_suggestions": ["扩容连接池"]
}
```"""
    result = parse_with_retry(raw, DiagnosisChainOutput)

    assert result["ok"] is True
    assert result["data"]["root_cause"] == "数据库连接池耗尽"
    assert result["data"]["confidence"] == 0.7


def test_parse_with_retry_invalid_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """非法文本解析失败并返回错误信息。"""
    # 全程 mock LLM：关闭可选的 json_repair 修复路径，使断言不受环境中真实 API Key 影响。
    monkeypatch.setattr(llm_manager, "get_llm", lambda *a, **k: None)
    result = parse_with_retry("这不是 JSON，也没有结构化内容", ReportChainOutput)

    assert result["ok"] is False
    assert "error" in result
    assert "raw_preview" in result


def test_parse_with_retry_empty_input() -> None:
    """空输入返回明确错误。"""
    result = parse_with_retry("", ReportChainOutput)

    assert result["ok"] is False
    assert result["error"] == "输入为空"


# ---------------------------------------------------------------------------
# evidence_builder
# ---------------------------------------------------------------------------


def test_evidence_builder_respects_max_logs() -> None:
    """sampled_count 不超过 max_logs 上限。"""
    logs = [_make_log("INFO", service=f"svc-{i}", log_id=f"log-{i}") for i in range(100)]
    max_logs = 10

    result = evidence_builder.build_evidence_package(logs, max_logs=max_logs)

    assert result["ok"] is True
    assert result["sampled_count"] <= max_logs
    assert result["input_log_count"] == 100


def test_evidence_builder_error_priority_sampling() -> None:
    """采样优先保留 ERROR 级别日志。"""
    logs = [_make_log("INFO", service=f"info-{i}") for i in range(20)]
    logs += [
        _make_log("ERROR", service="pay-svc", error_code="PAY_FAIL"),
        _make_log("ERROR", service="order-svc", error_code="ORD_FAIL"),
        _make_log("ERROR", service="inv-svc", error_code="INV_FAIL"),
        _make_log("ERROR", service="user-svc", error_code="USR_FAIL"),
    ]

    result = evidence_builder.build_evidence_package(logs, max_logs=3)
    samples = result["evidence_package"]["samples"]

    assert result["sampled_count"] == 3
    assert all(s["log_level"] == "ERROR" for s in samples)


def test_evidence_builder_empty_input() -> None:
    """空日志输入返回空证据包。"""
    result = evidence_builder.build_evidence_package([], metrics={"request_total": 0})

    assert result["ok"] is True
    assert result["input_log_count"] == 0
    assert result["sampled_count"] == 0
    assert result["evidence_package"]["samples"] == []
    _assert_no_placeholder(result)


# ---------------------------------------------------------------------------
# chain_schemas
# ---------------------------------------------------------------------------


def test_report_chain_output_model_validate() -> None:
    """ReportChainOutput 可 model_validate 合法数据。"""
    model = ReportChainOutput.model_validate(_REPORT_LLM_DATA)

    assert model.report_type.value == "periodic"
    assert model.title == "测试周期报告"
    assert model.risk_level == "medium"
    assert model.key_findings == ["发现 A"]


def test_diagnosis_chain_output_model_validate() -> None:
    """DiagnosisChainOutput 可 model_validate 并钳制 confidence。"""
    model = DiagnosisChainOutput.model_validate(_DIAGNOSIS_LLM_DATA)

    assert model.root_cause == "支付服务超时导致失败"
    assert model.confidence == 0.85
    assert model.severity.value == "high"

    clamped = DiagnosisChainOutput.model_validate({**_DIAGNOSIS_LLM_DATA, "confidence": 1.5})
    assert clamped.confidence == 1.0


# ---------------------------------------------------------------------------
# report_chain
# ---------------------------------------------------------------------------


def test_report_chain_llm_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """LLM 可用且解析成功时返回非降级报告。"""
    monkeypatch.setattr(llm_manager, "is_llm_available", lambda: True)
    monkeypatch.setattr(
        llm_manager,
        "invoke_structured",
        lambda task, prompt, schema: {"ok": True, "data": _REPORT_LLM_DATA},
    )

    result = report_chain.generate_periodic_report(_SAMPLE_EVIDENCE_PACKAGE)

    assert result["ok"] is True
    assert result["degraded"] is False
    assert result["title"] == "测试周期报告"
    assert result["risk_level"] == "medium"
    _assert_no_placeholder(result)


def test_report_chain_degraded_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """LLM 不可用时走模板降级路径。"""
    monkeypatch.setattr(llm_manager, "is_llm_available", lambda: False)

    result = report_chain.generate_periodic_report(_SAMPLE_EVIDENCE_PACKAGE)

    assert result["ok"] is True
    assert result["degraded"] is True
    assert result["report_type"] == "periodic"
    assert result["title"]
    assert result["summary"]
    assert isinstance(result["key_findings"], list)
    _assert_no_placeholder(result)


# ---------------------------------------------------------------------------
# diagnosis_chain
# ---------------------------------------------------------------------------


def test_diagnosis_chain_llm_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """LLM 可用时 infer_root_cause 返回结构化诊断。"""
    monkeypatch.setattr(llm_manager, "is_llm_available", lambda: True)
    monkeypatch.setattr(
        llm_manager,
        "invoke_structured",
        lambda task, prompt, schema: {"ok": True, "data": _DIAGNOSIS_LLM_DATA},
    )

    result = infer_root_cause(_SAMPLE_EVIDENCE_PACKAGE)

    assert result["ok"] is True
    assert result["degraded"] is False
    assert result["root_cause"] == "支付服务超时导致失败"
    assert result["confidence"] == 0.85
    _assert_no_placeholder(result)


def test_diagnosis_chain_degraded_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """LLM 不可用时 infer_root_cause 走规则降级。"""
    monkeypatch.setattr(llm_manager, "is_llm_available", lambda: False)

    result = infer_root_cause(_SAMPLE_EVIDENCE_PACKAGE)

    assert result["ok"] is True
    assert result["degraded"] is True
    assert "规则推断" in result["root_cause"]
    assert result["confidence"] == 0.4
    assert result["affected_services"]
    _assert_no_placeholder(result)


def test_generate_event_report_degraded_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """generate_event_report 在降级路径下产出事件报告字段。"""
    monkeypatch.setattr(llm_manager, "is_llm_available", lambda: False)

    result = generate_event_report(_SAMPLE_EVIDENCE_PACKAGE)

    assert result["ok"] is True
    assert result["degraded"] is True
    assert result["report_type"] == "event"
    assert result["title"]
    assert result["summary"] == result["root_cause"]
    _assert_no_placeholder(result)
