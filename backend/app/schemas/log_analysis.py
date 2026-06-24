"""日志分析相关的 Schema 定义。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    """日志条目。"""
    timestamp: str = Field(description="日志时间戳")
    message: str = Field(description="日志消息内容")
    level: str = Field(description="日志级别 (INFO/WARN/ERROR/DEBUG)")
    service: Optional[str] = Field(None, description="服务名称")
    host: Optional[str] = Field(None, description="主机名")


class LogPattern(BaseModel):
    """日志模式。"""
    pattern: str = Field(description="模式模板")
    count: int = Field(description="匹配次数")
    percentage: float = Field(description="占比百分比")
    examples: List[str] = Field(description="示例消息")
    severity_distribution: Dict[str, int] = Field(description="严重级别分布")


class LogPatternAnalysis(BaseModel):
    """日志模式分析结果。"""
    total_logs: int = Field(description="日志总数")
    unique_patterns: int = Field(description="唯一模式数")
    patterns: List[LogPattern] = Field(description="模式列表")
    summary: str = Field(description="分析摘要")


class PatternMatch(BaseModel):
    """模式匹配结果。"""
    pattern: str = Field(description="模式模板")
    count: int = Field(description="匹配次数")
    percentage: float = Field(description="占比百分比")
    first_occurrence: str = Field(description="首次出现时间")
    level: str = Field(description="日志级别")
    message: str = Field(description="原始消息")


class LogCluster(BaseModel):
    """日志聚类。"""
    cluster_id: str = Field(description="聚类ID")
    pattern: str = Field(description="聚类模式")
    count: int = Field(description="聚类中的日志数量")
    logs: List[LogEntry] = Field(description="聚类中的日志条目")
    severity_distribution: Dict[str, int] = Field(description="严重级别分布")
    representative: str = Field(description="代表性消息")


class ClusterResult(BaseModel):
    """聚类分析结果。"""
    total_clusters: int = Field(description="聚类总数")
    total_logs: int = Field(description="日志总数")
    clusters: List[LogCluster] = Field(description="聚类列表")
    summary: str = Field(description="分析摘要")


class LogAnalysisRequest(BaseModel):
    """日志分析请求。"""
    logs: List[LogEntry] = Field(description="日志条目列表")
    top_n: Optional[int] = Field(10, description="返回前N个模式")
    anomaly_threshold: Optional[float] = Field(0.05, description="异常阈值")
    max_clusters: Optional[int] = Field(10, description="最大聚类数")


class LogAnalysisResponse(BaseModel):
    """日志分析响应。"""
    pattern_analysis: LogPatternAnalysis = Field(description="模式分析结果")
    anomaly_patterns: List[PatternMatch] = Field(description="异常模式列表")
    cluster_result: ClusterResult = Field(description="聚类分析结果")
    summary: str = Field(description="综合摘要")
