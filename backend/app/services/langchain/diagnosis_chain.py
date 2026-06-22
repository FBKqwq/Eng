"""事件根因诊断 Chain。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.5 infer_root_cause 节点
职责：证据包 → 根因推断 + 事件诊断报告；LLM 不可用时降级为规则结论。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.schemas.diagnosis import SeverityLevel
from app.schemas.report import ReportType
from app.services.langchain import llm_manager, prompts
from app.services.langchain.chain_schemas import DiagnosisChainOutput

logger = logging.getLogger(__name__)

_DEGRADED_CONFIDENCE = 0.4


def infer_root_cause(evidence_package: dict[str, Any]) -> dict[str, Any]:
    """基于证据包推断根因；LLM 不可用时降级为规则结论。"""
    diagnosis, degraded, ok = _resolve_diagnosis(evidence_package)
    result = _diagnosis_to_dict(diagnosis)
    result["ok"] = ok
    result["degraded"] = degraded
    return result


def generate_event_report(evidence_package: dict[str, Any]) -> dict[str, Any]:
    """生成事件诊断报告；与 infer_root_cause 共用一次诊断解析，避免重复 LLM 调用。"""
    diagnosis, degraded, ok = _resolve_diagnosis(evidence_package)
    summary = _normalize_evidence_package(evidence_package)
    title = _build_event_title(diagnosis, summary)

    result = _diagnosis_to_dict(diagnosis)
    result.update(
        {
            "ok": ok,
            "degraded": degraded,
            "report_type": ReportType.event.value,
            "title": title,
            "summary": diagnosis.root_cause,
        }
    )
    return result


def _resolve_diagnosis(
    evidence_package: dict[str, Any],
) -> tuple[DiagnosisChainOutput, bool, bool]:
    """执行诊断解析：优先 LLM，失败或不可用时规则降级。"""
    package = _normalize_evidence_package(evidence_package)

    try:
        if llm_manager.is_llm_available():
            llm_result = _invoke_llm_diagnosis(package)
            if llm_result.get("ok") and llm_result.get("data"):
                validated = DiagnosisChainOutput.model_validate(llm_result["data"])
                return validated, False, True
            logger.info(
                "diagnosis_chain LLM 路径未成功，降级为规则结论 reason=%s",
                llm_result.get("error") or llm_result.get("reason"),
            )
    except Exception:
        logger.exception("diagnosis_chain LLM 调用异常，降级为规则结论")

    return _rule_degrade_diagnosis(package), True, True


def _invoke_llm_diagnosis(package: dict[str, Any]) -> dict[str, Any]:
    """通过 llm_manager 发起结构化诊断调用。"""
    template = prompts.get_prompt("diagnosis")
    if not template:
        return {"ok": False, "reason": "prompt_missing"}

    prompt = template.format(
        evidence_package=json.dumps(package, ensure_ascii=False, default=str)
    )
    return llm_manager.invoke_structured("diagnosis", prompt, DiagnosisChainOutput)


def _rule_degrade_diagnosis(package: dict[str, Any]) -> DiagnosisChainOutput:
    """基于 top_error_codes / top_services 与指标给出规则化根因。"""
    summary = package.get("summary") or {}
    grouped = package.get("grouped") or {}
    metrics = package.get("metrics") or {}

    top_error_codes = _as_str_list(summary.get("top_error_codes"))
    top_services = _as_str_list(summary.get("top_services"))
    error_count = int(summary.get("error_count") or 0)
    warn_count = int(summary.get("warn_count") or 0)

    affected_services = top_services[:5] if top_services else []
    evidence_refs = _build_evidence_refs(top_error_codes, grouped, summary)

    if top_error_codes and top_services:
        root_cause = (
            f"规则推断：错误码 {', '.join(top_error_codes[:3])} "
            f"在 {', '.join(top_services[:3])} 等服务中集中出现，"
            f"共 {error_count} 条 ERROR、{warn_count} 条 WARN，需优先排查相关依赖与调用链。"
        )
    elif top_error_codes:
        root_cause = (
            f"规则推断：主要异常为错误码 {', '.join(top_error_codes[:3])}，"
            f"共 {error_count} 条 ERROR，建议对照该错误码的已知处置手册排查。"
        )
    elif top_services:
        root_cause = (
            f"规则推断：异常日志主要集中于 {', '.join(top_services[:3])}，"
            f"共 {error_count} 条 ERROR，建议检查该服务近期变更与下游依赖。"
        )
    elif error_count > 0 or warn_count > 0:
        root_cause = (
            f"规则推断：证据包含 {error_count} 条 ERROR、{warn_count} 条 WARN，"
            "但未形成明显错误码或服务聚集模式，建议人工复核样本日志。"
        )
    else:
        root_cause = "规则推断：当前证据包未发现明确异常模式，建议扩大时间窗口或补充上下文日志。"

    return DiagnosisChainOutput(
        root_cause=root_cause,
        confidence=_DEGRADED_CONFIDENCE,
        severity=_infer_severity_from_metrics(error_count, warn_count, metrics),
        affected_services=affected_services,
        evidence_refs=evidence_refs,
        action_suggestions=_build_action_suggestions(top_error_codes, top_services, error_count),
    )


def _diagnosis_to_dict(diagnosis: DiagnosisChainOutput) -> dict[str, Any]:
    """将 DiagnosisChainOutput 转为可 JSON 序列化的 dict。"""
    payload = diagnosis.model_dump()
    severity = payload.get("severity")
    if isinstance(severity, SeverityLevel):
        payload["severity"] = severity.value
    return payload


def _normalize_evidence_package(evidence_package: dict[str, Any]) -> dict[str, Any]:
    """兼容 build_evidence_package 外层包装与直接传入内层 evidence_package。"""
    if not evidence_package:
        return {}
    inner = evidence_package.get("evidence_package")
    if isinstance(inner, dict):
        return inner
    return evidence_package


def _as_str_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if item]
    return []


def _build_evidence_refs(
    top_error_codes: list[str],
    grouped: dict[str, Any],
    summary: dict[str, Any],
) -> list[str]:
    """从分组统计构建可引用的证据摘要。"""
    refs: list[str] = []
    by_error_code = grouped.get("by_error_code") or {}
    by_service = grouped.get("by_service") or {}

    for code in top_error_codes[:5]:
        count = by_error_code.get(code)
        if count is not None:
            refs.append(f"{code} x{count}")
        else:
            refs.append(code)

    for service, count in list(by_service.items())[:3]:
        refs.append(f"{service} 日志 x{count}")

    error_count = summary.get("error_count")
    if error_count is not None:
        refs.append(f"ERROR 总数 {error_count}")

    return refs[:8]


def _infer_severity_from_metrics(
    error_count: int,
    warn_count: int,
    metrics: dict[str, Any],
) -> SeverityLevel:
    """根据错误量与指标规则推断严重等级。"""
    error_rate = metrics.get("error_rate")
    if isinstance(error_rate, (int, float)) and error_rate >= 0.1:
        return SeverityLevel.critical
    if error_count >= 50:
        return SeverityLevel.critical
    if error_count >= 10 or (isinstance(error_rate, (int, float)) and error_rate >= 0.05):
        return SeverityLevel.high
    if error_count > 0:
        return SeverityLevel.medium
    if warn_count > 0:
        return SeverityLevel.low
    return SeverityLevel.low


def _build_action_suggestions(
    top_error_codes: list[str],
    top_services: list[str],
    error_count: int,
) -> list[str]:
    """基于统计特征生成规则化处置建议。"""
    suggestions: list[str] = []

    if top_services:
        suggestions.append(f"优先检查服务 {top_services[0]} 的近期部署、配置变更与依赖健康状态。")
    if top_error_codes:
        suggestions.append(f"针对错误码 {top_error_codes[0]} 检索历史工单与 Runbook，核对上下游超时与重试策略。")
    if error_count > 0:
        suggestions.append("拉取相关 trace_id 的完整调用链，确认失败节点与级联影响范围。")
    if not suggestions:
        suggestions.append("扩大采样时间窗口或补充关联服务日志后重新诊断。")

    return suggestions[:5]


def _build_event_title(diagnosis: DiagnosisChainOutput, summary: dict[str, Any]) -> str:
    """生成事件诊断报告标题。"""
    services = diagnosis.affected_services or _as_str_list(summary.get("top_services"))
    codes = _as_str_list(summary.get("top_error_codes"))

    if services and codes:
        return f"事件诊断：{services[0]} · {codes[0]}"
    if services:
        return f"事件诊断：{services[0]} 异常"
    if codes:
        return f"事件诊断：{codes[0]}"
    return "事件诊断报告"
