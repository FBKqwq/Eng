"""预警解释 Chain。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.3 alert_decision 节点
职责：候选预警 → 可解释文案；LLM 不可用时退化为基于 alert_type/affected_service/severity 的模板。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel, Field

from app.services.langchain import llm_manager, prompts

logger = logging.getLogger(__name__)

_SEVERITY_LABELS: dict[str, str] = {
    "low": "低",
    "medium": "中",
    "high": "高",
    "critical": "严重",
}

_ALERT_TYPE_LABELS: dict[str, str] = {
    "pay_fail": "支付失败",
    "error_spike": "错误激增",
    "latency_spike": "延迟异常",
    "unknown": "未知异常",
}


class _AlertLlmOutput(BaseModel):
    """对齐 ALERT_PROMPT 的结构化输出，供 invoke_structured 解析。"""

    title: str = ""
    description: str = ""
    severity: str = "medium"
    impact_scope: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    evidence_summary: str = ""


def explain_alert(alert_candidate: dict[str, Any]) -> dict[str, Any]:
    """为候选预警生成可解释文案；LLM 不可用或解析失败时降级为模板文案。"""
    candidate = alert_candidate if isinstance(alert_candidate, dict) else {}

    try:
        if llm_manager.is_llm_available():
            llm_result = _invoke_llm_alert(candidate)
            if llm_result.get("ok") and llm_result.get("data"):
                return _build_llm_response(llm_result["data"], candidate)
    except Exception:
        logger.exception("explain_alert LLM 路径异常，降级为模板文案")

    return _build_template_alert(candidate)


def _invoke_llm_alert(candidate: dict[str, Any]) -> dict[str, Any]:
    """通过 llm_manager 发起结构化预警文案调用。"""
    template = prompts.get_prompt("alert")
    if not template:
        return {"ok": False, "error": "alert prompt 未配置"}

    alert_context = json.dumps(candidate, ensure_ascii=False, default=str)
    prompt = template.format(alert_context=alert_context)
    return llm_manager.invoke_structured("alert", prompt, _AlertLlmOutput)


def _build_llm_response(data: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """将 LLM 结构化输出映射为 explain_alert 契约字段。"""
    validated = _AlertLlmOutput.model_validate(data)
    title = validated.title.strip() or _build_title_from_candidate(candidate, validated.severity)
    detail = _compose_detail_from_llm(validated)
    return {
        "ok": True,
        "degraded": False,
        "title": title,
        "detail": detail,
    }


def _build_title_from_candidate(candidate: dict[str, Any], llm_severity: str = "") -> str:
    """当 LLM 未返回标题时，基于候选预警字段拼接标题。"""
    alert_type = _coerce_str(candidate.get("alert_type")).lower() or "unknown"
    service = _coerce_str(candidate.get("affected_service")) or "未知服务"
    severity = _coerce_str(llm_severity or candidate.get("severity")).lower() or "medium"
    type_label = _ALERT_TYPE_LABELS.get(alert_type, alert_type.replace("_", " "))
    severity_label = _SEVERITY_LABELS.get(severity, severity)
    return f"{service} {type_label}预警（{severity_label}级）"


def _compose_detail_from_llm(output: _AlertLlmOutput) -> str:
    """将 LLM 多字段说明合并为 detail 段落。"""
    parts: list[str] = []
    if output.description.strip():
        parts.append(output.description.strip())
    if output.evidence_summary.strip():
        parts.append(f"关键证据：{output.evidence_summary.strip()}")
    if output.impact_scope:
        parts.append(f"影响范围：{', '.join(str(s) for s in output.impact_scope[:5])}")
    if output.suggested_actions:
        actions = "；".join(str(a) for a in output.suggested_actions[:5])
        parts.append(f"建议处置：{actions}")
    if parts:
        return "".join(parts)
    return "系统检测到异常预警，请结合关联日志进一步排查。"


def _build_template_alert(candidate: dict[str, Any]) -> dict[str, Any]:
    """基于 alert_type / affected_service / severity 生成规则化预警文案。"""
    alert_type = _coerce_str(candidate.get("alert_type")).lower() or "unknown"
    service = _coerce_str(candidate.get("affected_service")) or "未知服务"
    severity = _coerce_str(candidate.get("severity")).lower() or "medium"

    type_label = _ALERT_TYPE_LABELS.get(alert_type, alert_type.replace("_", " "))
    severity_label = _SEVERITY_LABELS.get(severity, severity)

    title = _build_title_from_candidate(candidate)

    detail_parts = [
        f"检测到「{type_label}」类型预警，影响服务 {service}，严重等级为 {severity_label}（{severity}）。",
    ]

    existing_desc = _coerce_str(candidate.get("description"))
    if existing_desc:
        detail_parts.append(existing_desc)

    if severity in ("high", "critical"):
        detail_parts.append("建议立即排查相关服务依赖、近期变更与错误日志样本。")
    elif severity == "medium":
        detail_parts.append("建议关注异常趋势，确认是否为偶发或持续恶化。")
    else:
        detail_parts.append("建议纳入常规巡检跟进。")

    detail_parts.append("（本说明由规则模板生成，LLM 未参与或解析失败。）")

    return {
        "ok": True,
        "degraded": True,
        "title": title,
        "detail": "".join(detail_parts),
    }


def _coerce_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
