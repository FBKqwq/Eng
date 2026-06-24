"""预测与异常检测相关 Schema。

职责：定义时序异常检测与趋势预测的请求/响应契约。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# =========================
# Enums
# =========================

class AnomalyMethod(str, Enum):
    """异常检测方法。"""
    zscore = "zscore"
    iqr = "iqr"
    mad = "mad"


class PredictionMethod(str, Enum):
    """趋势预测方法。"""
    linear = "linear"
    moving_average = "moving_average"
    exponential_smoothing = "exponential_smoothing"


class AnomalyLevel(str, Enum):
    """异常严重程度。"""
    normal = "normal"
    warning = "warning"
    critical = "critical"


# =========================
# 异常检测请求/响应
# =========================

class TimeSeriesPoint(BaseModel):
    """时序数据点。"""
    timestamp: str = Field(..., description="ISO 8601 格式时间戳")
    value: float = Field(..., description="指标值")


class AnomalyDetectRequest(BaseModel):
    """时序异常检测请求。"""
    metric_name: str = Field(..., description="指标名称，如 error_rate")
    data: list[TimeSeriesPoint] = Field(..., min_length=3, description="时序数据点列表，至少 3 个点")
    method: AnomalyMethod = Field(default=AnomalyMethod.zscore, description="检测方法")
    threshold: float = Field(default=2.0, ge=0.5, le=5.0, description="异常阈值倍数（如 zscore 的 2σ）")
    sensitivity: float = Field(default=1.0, ge=0.1, le=3.0, description="灵敏度系数，越大越敏感")

    @field_validator("data")
    @classmethod
    def validate_data_length(cls, value: list[TimeSeriesPoint]) -> list[TimeSeriesPoint]:
        if len(value) < 3:
            raise ValueError("时序数据至少需要 3 个点")
        return value


class AnomalyPoint(BaseModel):
    """异常点详情。"""
    timestamp: str
    value: float
    expected: float = Field(..., description="预期值")
    deviation: float = Field(..., description="偏离程度（标准差倍数或比例）")
    level: AnomalyLevel
    reason: str = Field(default="", description="异常原因简述")


class AnomalyDetectData(BaseModel):
    """异常检测响应负载。"""
    metric_name: str
    method: AnomalyMethod
    total_points: int
    anomaly_count: int
    anomaly_ratio: float = Field(..., ge=0.0, le=1.0, description="异常点占比")
    anomalies: list[AnomalyPoint]
    stats: dict[str, float] = Field(default_factory=dict, description="统计摘要（mean/std/min/max）")
    summary: str = Field(default="", description="检测结论摘要")


# =========================
# 趋势预测请求/响应
# =========================

class TrendPredictRequest(BaseModel):
    """趋势预测请求。"""
    metric_name: str = Field(..., description="指标名称")
    data: list[TimeSeriesPoint] = Field(..., min_length=3, description="历史时序数据")
    method: PredictionMethod = Field(default=PredictionMethod.linear, description="预测方法")
    forecast_steps: int = Field(default=5, ge=1, le=30, description="预测未来步数")
    interval_minutes: int = Field(default=5, ge=1, le=1440, description="数据点间隔分钟数")

    @field_validator("data")
    @classmethod
    def validate_data_length(cls, value: list[TimeSeriesPoint]) -> list[TimeSeriesPoint]:
        if len(value) < 3:
            raise ValueError("历史数据至少需要 3 个点")
        return value


class PredictedPoint(BaseModel):
    """预测点详情。"""
    timestamp: str
    predicted_value: float
    lower_bound: Optional[float] = Field(default=None, description="预测下限")
    upper_bound: Optional[float] = Field(default=None, description="预测上限")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="置信度")


class TrendPredictData(BaseModel):
    """趋势预测响应负载。"""
    metric_name: str
    method: PredictionMethod
    historical_count: int
    forecast_steps: int
    predictions: list[PredictedPoint]
    trend_direction: str = Field(..., description="趋势方向：up/down/stable")
    trend_strength: float = Field(..., ge=0.0, le=1.0, description="趋势强度")
    summary: str = Field(default="", description="预测结论摘要")


# =========================
# 综合预测门面请求/响应
# =========================

class PredictionRequest(BaseModel):
    """综合预测请求（异常检测 + 趋势预测）。"""
    metric_name: str
    data: list[TimeSeriesPoint]
    detect_method: AnomalyMethod = AnomalyMethod.zscore
    predict_method: PredictionMethod = PredictionMethod.linear
    forecast_steps: int = 5
    threshold: float = 2.0
    interval_minutes: int = 5


class PredictionData(BaseModel):
    """综合预测响应负载。"""
    metric_name: str
    anomaly: Optional[AnomalyDetectData] = None
    trend: Optional[TrendPredictData] = None
    combined_summary: str = Field(default="", description="综合分析结论")
