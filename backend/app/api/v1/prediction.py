"""预测与异常检测 API。

接口：
- POST /api/v1/prediction/anomaly — 时序异常检测
- POST /api/v1/prediction/trend   — 趋势预测
- POST /api/v1/prediction         — 综合预测（异常检测 + 趋势预测）

职责：薄路由层，只接请求、校验、调 service、返回统一信封。
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.prediction import (
    AnomalyDetectData,
    AnomalyDetectRequest,
    PredictionData,
    PredictionRequest,
    TrendPredictData,
    TrendPredictRequest,
)
from app.schemas.response import ApiCode, ApiResponse, error_envelope, ok_envelope
from app.services.yc.yx.anomaly_detector import detect_anomalies
from app.services.yc.yx.trend_predictor import predict_trend

router = APIRouter()


@router.post("/anomaly", response_model=ApiResponse[AnomalyDetectData])
def anomaly_detect(payload: AnomalyDetectRequest) -> ApiResponse[AnomalyDetectData]:
    """时序异常检测。

    基于统计方法（Z-Score / IQR / MAD）识别时序数据中的异常点。
    """
    try:
        result = detect_anomalies(payload)
        return ok_envelope(result)
    except Exception as e:
        return error_envelope(
            ApiCode.INTERNAL_ERROR,
            f"异常检测失败：{str(e)}",
        )


@router.post("/trend", response_model=ApiResponse[TrendPredictData])
def trend_predict(payload: TrendPredictRequest) -> ApiResponse[TrendPredictData]:
    """趋势预测。

    基于历史时序数据预测未来走势（线性回归 / 移动平均 / 指数平滑）。
    """
    try:
        result = predict_trend(payload)
        return ok_envelope(result)
    except Exception as e:
        return error_envelope(
            ApiCode.INTERNAL_ERROR,
            f"趋势预测失败：{str(e)}",
        )


@router.post("", response_model=ApiResponse[PredictionData])
def prediction(payload: PredictionRequest) -> ApiResponse[PredictionData]:
    """综合预测（异常检测 + 趋势预测）。

    一次性执行异常检测和趋势预测，返回综合分析结果。
    """
    try:
        # 异常检测
        anomaly_request = AnomalyDetectRequest(
            metric_name=payload.metric_name,
            data=payload.data,
            method=payload.detect_method,
            threshold=payload.threshold,
        )
        anomaly_result = detect_anomalies(anomaly_request)

        # 趋势预测
        trend_request = TrendPredictRequest(
            metric_name=payload.metric_name,
            data=payload.data,
            method=payload.predict_method,
            forecast_steps=payload.forecast_steps,
            interval_minutes=payload.interval_minutes,
        )
        trend_result = predict_trend(trend_request)

        # 综合摘要
        combined_summary = _build_combined_summary(anomaly_result, trend_result)

        return ok_envelope(
            PredictionData(
                metric_name=payload.metric_name,
                anomaly=anomaly_result,
                trend=trend_result,
                combined_summary=combined_summary,
            )
        )
    except Exception as e:
        return error_envelope(
            ApiCode.INTERNAL_ERROR,
            f"综合预测失败：{str(e)}",
        )


def _build_combined_summary(anomaly: AnomalyDetectData, trend: TrendPredictData) -> str:
    """构建综合分析摘要。"""
    parts: list[str] = []

    if anomaly.anomaly_count > 0:
        parts.append(f"检测到 {anomaly.anomaly_count} 个异常点（{anomaly.anomaly_ratio:.1%}）")
    else:
        parts.append("未检测到异常")

    parts.append(f"趋势预测：{trend.trend_direction}（强度 {trend.trend_strength:.2f}）")

    return "；".join(parts)
