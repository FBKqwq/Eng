"""智能根因分析数据模型"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DiagnosisStep(BaseModel):
    """诊断步骤"""
    name: str = Field(description="步骤名称")
    status: str = Field(description="状态: pending/completed/failed")
    result: dict = Field(default_factory=dict, description="步骤结果")
    timestamp: datetime = Field(description="时间戳")


class RootCause(BaseModel):
    """根因分析结果"""
    cause: str = Field(description="根因描述")
    confidence: float = Field(description="置信度 0-1")
    pattern: str = Field(description="匹配的问题模式")
    related_metrics: List[str] = Field(description="相关指标")


class Solution(BaseModel):
    """解决方案"""
    cause: str = Field(description="对应的根因")
    solution: str = Field(description="解决方案描述")
    confidence: float = Field(description="置信度")
    priority: str = Field(description="优先级: high/medium/low")


class RootCauseAnalysisRequest(BaseModel):
    """根因分析请求"""
    problem_description: str = Field(description="问题描述")
    context: Optional[dict] = Field(default=None, description="上下文信息")


class RootCauseAnalysisResponse(BaseModel):
    """根因分析响应"""
    analysis_id: str = Field(description="分析ID")
    status: str = Field(description="分析状态")
    steps: List[DiagnosisStep] = Field(description="诊断步骤")
    root_causes: List[RootCause] = Field(description="可能的根因列表")
    solutions: List[Solution] = Field(description="解决方案列表")
    confidence: float = Field(description="整体置信度")
    summary: str = Field(description="分析摘要")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class SolutionFeedbackRequest(BaseModel):
    """解决方案反馈请求"""
    solution_index: int = Field(description="解决方案索引")
    feedback: str = Field(description="反馈内容")
