"""集中 Prompt 模板（占位）。

职责：周期报告 / 根因诊断 / 关系发现 / 预警解释 / 证据摘要五类 Prompt。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.6
状态：占位 — 模板常量待 M3 填充。
"""

from __future__ import annotations

REPORT_PROMPT = "[占位] 周期报告生成 Prompt，待 M3 实现"
DIAGNOSIS_PROMPT = "[占位] 根因诊断 Prompt，待 M3 实现"
RELATION_PROMPT = "[占位] 隐藏关系发现 Prompt，待 M7 实现"
ALERT_PROMPT = "[占位] 预警解释 Prompt，待 M3 实现"
EVIDENCE_SUMMARY_PROMPT = "[占位] 证据摘要 Prompt，待 M3 实现"


def get_prompt(name: str) -> str:
    """按名称获取 Prompt 模板（占位）。"""
    mapping = {
        "report": REPORT_PROMPT,
        "diagnosis": DIAGNOSIS_PROMPT,
        "relation": RELATION_PROMPT,
        "alert": ALERT_PROMPT,
        "evidence_summary": EVIDENCE_SUMMARY_PROMPT,
    }
    return mapping.get(name, f"[占位] 未知 Prompt: {name}")
