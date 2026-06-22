"""周期报告 Chain。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.4 generate_report 节点
职责：证据包 → 周期分析报告；LLM 不可用时退化为基于 summary/metrics 的模板报告。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.services.langchain import llm_manager, prompts
from app.services.langchain.chain_schemas import ReportChainOutput, ReportRiskLevel

logger = logging.getLogger(__name__)

_HIGH_ERROR_COUNT = 10
_HIGH_ERROR_RATE = 0.05
_MEDIUM_WARN_COUNT = 3


def generate_periodic_report(evidence_package: dict[str, Any]) -> dict[str, Any]:
    """基于证据包生成周期分析报告；LLM 不可用或解析失败时降级为模板报告。"""
    package = _normalize_evidence_package(evidence_package)

    try:
        if llm_manager.is_llm_available():
            llm_result = _invoke_llm_report(package)
            if llm_result.get("ok") and llm_result.get("data"):
                return _build_response(llm_result["data"], degraded=False)
    except Exception:
        logger.exception("generate_periodic_report LLM 路径异常，降级为模板报告")

    return _build_template_report(package)


def _normalize_evidence_package(raw: dict[str, Any]) -> dict[str, Any]:
    """兼容直接传入内层 evidence_package 或 build_evidence_package 完整返回值。"""
    if "summary" in raw:
        return raw
    inner = raw.get("evidence_package")
    if isinstance(inner, dict):
        return inner
    return raw


def _invoke_llm_report(package: dict[str, Any]) -> dict[str, Any]:
    """调用 LLM 生成结构化周期报告。"""
    template = prompts.get_prompt("report")
    if not template:
        return {"ok": False, "error": "report prompt 未配置"}

    evidence_json = json.dumps(package, ensure_ascii=False, default=str)
    prompt = template.format(evidence_package=evidence_json)
    return llm_manager.invoke_structured("report", prompt, ReportChainOutput)


def _build_response(data: dict[str, Any], *, degraded: bool) -> dict[str, Any]:
    """校验并组装符合 ReportChainOutput 的返回 dict。"""
    validated = ReportChainOutput.model_validate(data)
    return {
        "ok": True,
        "degraded": degraded,
        **validated.model_dump(mode="json"),
    }


def _build_template_report(package: dict[str, Any]) -> dict[str, Any]:
    """基于证据包 summary/metrics 规则拼接降级报告。"""
    summary = package.get("summary") or {}
    metrics = package.get("metrics") or {}
    grouped = package.get("grouped") or {}
    samples = package.get("samples") or []

    risk_level = _infer_risk_level(summary, metrics)
    key_findings = _build_key_findings(summary, grouped, samples)
    recommendations = _build_recommendations(risk_level, summary, metrics)
    report_summary = _build_summary_text(summary, metrics, risk_level)

    title = _build_title(risk_level, summary)

    payload = ReportChainOutput(
        report_type="periodic",
        title=title,
        risk_level=risk_level,
        summary=report_summary,
        key_findings=key_findings,
        recommendations=recommendations,
    )
    return {
        "ok": True,
        "degraded": True,
        **payload.model_dump(mode="json"),
    }


def _infer_risk_level(summary: dict[str, Any], metrics: dict[str, Any]) -> ReportRiskLevel:
    """由 summary/metrics 指标规则推断风险等级。"""
    error_count = _coerce_int(summary.get("error_count"))
    warn_count = _coerce_int(summary.get("warn_count"))
    total_logs = _coerce_int(summary.get("total_logs"))
    error_rate = _resolve_error_rate(summary, metrics, total_logs, error_count)

    if error_count >= _HIGH_ERROR_COUNT:
        return "high"
    if error_rate is not None and error_rate >= _HIGH_ERROR_RATE:
        return "high"
    if error_count > 0:
        return "medium"
    if warn_count >= _MEDIUM_WARN_COUNT:
        return "medium"
    if warn_count > 0:
        return "low"
    return "low"


def _resolve_error_rate(
    summary: dict[str, Any],
    metrics: dict[str, Any],
    total_logs: int,
    error_count: int,
) -> float | None:
    """从 metrics 或 summary 推导错误率。"""
    for source in (metrics, summary):
        rate = source.get("error_rate")
        if rate is not None:
            try:
                return float(rate)
            except (TypeError, ValueError):
                continue
    if total_logs > 0:
        return error_count / total_logs
    return None


def _build_title(risk_level: ReportRiskLevel, summary: dict[str, Any]) -> str:
    """生成降级报告标题。"""
    labels = {"low": "运行平稳", "medium": "存在需关注异常", "high": "风险偏高"}
    total = _coerce_int(summary.get("total_logs"))
    return f"周期健康报告（{labels.get(risk_level, '待评估')}，共 {total} 条日志）"


def _build_summary_text(
    summary: dict[str, Any],
    metrics: dict[str, Any],
    risk_level: ReportRiskLevel,
) -> str:
    """拼接一段话总结。"""
    total = _coerce_int(summary.get("total_logs"))
    error_count = _coerce_int(summary.get("error_count"))
    warn_count = _coerce_int(summary.get("warn_count"))
    error_rate = _resolve_error_rate(summary, metrics, total, error_count)

    parts = [
        f"本周期共采集 {total} 条日志，ERROR {error_count} 条，WARN {warn_count} 条。",
    ]
    if error_rate is not None:
        parts.append(f"错误率约 {error_rate * 100:.2f}%。")
    risk_text = {"low": "整体风险较低", "medium": "存在一定异常需跟进", "high": "异常集中，建议优先处置"}
    parts.append(f"{risk_text.get(risk_level, '风险待评估')}（规则评估：{risk_level}）。")
    parts.append("本报告由统计模板生成（LLM 未参与或解析失败）。")
    return "".join(parts)


def _build_key_findings(
    summary: dict[str, Any],
    grouped: dict[str, Any],
    samples: list[dict[str, Any]],
) -> list[str]:
    """从证据包提炼关键发现。"""
    findings: list[str] = []

    total = _coerce_int(summary.get("total_logs"))
    error_count = _coerce_int(summary.get("error_count"))
    if total > 0:
        findings.append(f"日志总量 {total}，其中 ERROR {error_count} 条。")

    top_services = summary.get("top_services") or []
    if top_services:
        findings.append(f"日志量靠前服务：{', '.join(str(s) for s in top_services[:5])}。")

    top_codes = summary.get("top_error_codes") or []
    if top_codes:
        by_code = grouped.get("by_error_code") or {}
        code_parts = []
        for code in top_codes[:5]:
            count = by_code.get(code, "—")
            code_parts.append(f"{code}({count})")
        findings.append(f"高频错误码：{', '.join(code_parts)}。")

    for sample in samples[:3]:
        level = sample.get("log_level", "")
        service = sample.get("service_name", "unknown")
        message = (sample.get("message") or "")[:120]
        code = sample.get("error_code")
        code_part = f" [{code}]" if code else ""
        findings.append(f"样本 [{level}] {service}{code_part}：{message}")

    if not findings:
        findings.append("本周期无显著异常样本，系统运行平稳。")

    return findings


def _build_recommendations(
    risk_level: ReportRiskLevel,
    summary: dict[str, Any],
    metrics: dict[str, Any],
) -> list[str]:
    """按风险等级给出规则化运维建议。"""
    recs: list[str] = []
    top_services = summary.get("top_services") or []
    top_codes = summary.get("top_error_codes") or []

    if risk_level == "high":
        recs.append("优先排查 ERROR 集中服务与高频错误码，必要时启动应急预案。")
        if top_services:
            recs.append(f"重点检查服务：{', '.join(str(s) for s in top_services[:3])}。")
        if top_codes:
            recs.append(f"针对错误码 {', '.join(str(c) for c in top_codes[:3])} 检索关联 trace 与上下游依赖。")
    elif risk_level == "medium":
        recs.append("关注 WARN/ERROR 趋势，确认是否为偶发或持续恶化。")
        if top_codes:
            recs.append(f"对错误码 {top_codes[0]} 做窗口对比与根因初筛。")
    else:
        recs.append("维持常规巡检；可结合业务高峰时段做容量与延迟基线对比。")

    request_total = metrics.get("request_total") or metrics.get("total_requests")
    if request_total is not None:
        recs.append(f"本周期请求量约 {request_total}，可结合峰值时段观察延迟与错误关联。")

    return recs


def _coerce_int(value: Any) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
