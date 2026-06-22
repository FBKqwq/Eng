"""链层 LLM 结构化输出模型。

供 prompts / report_chain / diagnosis_chain / output_parsers 共用。
字段名与 prompts.py 模板一致，为本层字段真相源。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.6
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.diagnosis import SeverityLevel
from app.schemas.report import ReportType

ReportRiskLevel = Literal["low", "medium", "high"]


class ReportChainOutput(BaseModel):
    """周期报告 LLM 结构化输出（对齐 REPORT_PROMPT 字段）。"""

    report_type: ReportType = ReportType.periodic
    title: str = ""
    risk_level: ReportRiskLevel = "medium"
    summary: str = ""
    key_findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class DiagnosisChainOutput(BaseModel):
    """根因诊断 LLM 结构化输出（对齐 DIAGNOSIS_PROMPT 字段）。"""

    root_cause: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    severity: SeverityLevel = SeverityLevel.medium
    affected_services: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    action_suggestions: list[str] = Field(default_factory=list)

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value: object) -> float:
        """容忍 LLM 漏字段或越界数值，钳制到 [0, 1]。"""
        if value is None:
            return 0.0
        try:
            numeric = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, numeric))


RelationType = Literal["temporal_correlation", "causal_hypothesis", "co_occurrence"]


class RelationItem(BaseModel):
    """单条隐藏关系（对齐 RELATION_PROMPT 字段）。"""

    relation_type: RelationType = "temporal_correlation"
    description: str = ""
    entities: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value: object) -> float:
        """容忍 LLM 漏字段或越界数值，钳制到 [0, 1]。"""
        if value is None:
            return 0.0
        try:
            numeric = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, numeric))


class RelationChainOutput(BaseModel):
    """隐藏关系发现 LLM 结构化输出（对齐 RELATION_PROMPT 字段）。"""

    relations: list[RelationItem] = Field(default_factory=list)
