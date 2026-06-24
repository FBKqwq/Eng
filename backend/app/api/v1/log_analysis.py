"""日志分析 API。

接口：
- POST /api/v1/log_analysis/pattern — 日志模式分析
- POST /api/v1/log_analysis/anomaly — 异常模式检测
- POST /api/v1/log_analysis/cluster — 日志聚类分析
- POST /api/v1/log_analysis — 综合分析

职责：薄路由层，只接请求、校验、调 service、返回统一信封。
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.log_analysis import (
    ClusterResult,
    LogAnalysisRequest,
    LogAnalysisResponse,
    LogPatternAnalysis,
    PatternMatch,
)
from app.schemas.response import ApiCode, ApiResponse, error_envelope, ok_envelope
from app.services.yc.yy.log_pattern import analyze_log_patterns, detect_anomaly_patterns
from app.services.yc.yy.log_clustering import cluster_logs

router = APIRouter()


@router.post("/pattern", response_model=ApiResponse[LogPatternAnalysis])
def analyze_pattern(payload: LogAnalysisRequest) -> ApiResponse[LogPatternAnalysis]:
    """日志模式分析。

    提取日志中的常见模式模板，帮助识别重复出现的日志类型。
    """
    try:
        result = analyze_log_patterns(payload.logs, payload.top_n or 10)
        return ok_envelope(result)
    except Exception as e:
        return error_envelope(
            ApiCode.INTERNAL_ERROR,
            f"模式分析失败：{str(e)}",
        )


@router.post("/anomaly", response_model=ApiResponse[list[PatternMatch]])
def detect_anomaly(payload: LogAnalysisRequest) -> ApiResponse[list[PatternMatch]]:
    """异常模式检测。

    识别出现频率极低的异常日志模式。
    """
    try:
        result = detect_anomaly_patterns(payload.logs, payload.anomaly_threshold or 0.05)
        return ok_envelope(result)
    except Exception as e:
        return error_envelope(
            ApiCode.INTERNAL_ERROR,
            f"异常检测失败：{str(e)}",
        )


@router.post("/cluster", response_model=ApiResponse[ClusterResult])
def analyze_cluster(payload: LogAnalysisRequest) -> ApiResponse[ClusterResult]:
    """日志聚类分析。

    基于文本相似度对日志进行分组。
    """
    try:
        result = cluster_logs(payload.logs, payload.max_clusters or 10)
        return ok_envelope(result)
    except Exception as e:
        return error_envelope(
            ApiCode.INTERNAL_ERROR,
            f"聚类分析失败：{str(e)}",
        )


@router.post("", response_model=ApiResponse[LogAnalysisResponse])
def analyze_all(payload: LogAnalysisRequest) -> ApiResponse[LogAnalysisResponse]:
    """综合日志分析。

    一次性执行模式分析、异常检测和聚类分析。
    """
    try:
        # 模式分析
        pattern_result = analyze_log_patterns(payload.logs, payload.top_n or 10)
        
        # 异常检测
        anomaly_result = detect_anomaly_patterns(payload.logs, payload.anomaly_threshold or 0.05)
        
        # 聚类分析
        cluster_result = cluster_logs(payload.logs, payload.max_clusters or 10)
        
        # 综合摘要
        summary = f"分析完成：{len(payload.logs)} 条日志，{pattern_result.unique_patterns} 种模式，{len(anomaly_result)} 个异常模式，{cluster_result.total_clusters} 个聚类"

        return ok_envelope(
            LogAnalysisResponse(
                pattern_analysis=pattern_result,
                anomaly_patterns=anomaly_result,
                cluster_result=cluster_result,
                summary=summary
            )
        )
    except Exception as e:
        return error_envelope(
            ApiCode.INTERNAL_ERROR,
            f"综合分析失败：{str(e)}",
        )
