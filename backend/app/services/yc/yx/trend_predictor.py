"""趋势预测服务。

职责：基于历史时序数据预测未来趋势，支持线性回归、移动平均、指数平滑三种方法。
不依赖外部 ML 库，纯 Python 实现。
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import Optional

from app.schemas.prediction import (
    PredictedPoint,
    PredictionMethod,
    TrendPredictData,
    TrendPredictRequest,
)


def predict_trend(request: TrendPredictRequest) -> TrendPredictData:
    """执行趋势预测。

    根据 request.method 选择预测算法：
    - linear: 最小二乘法线性回归
    - moving_average: 简单移动平均
    - exponential_smoothing: 一次指数平滑
    """
    values = [p.value for p in request.data]
    timestamps = [p.timestamp for p in request.data]
    n = len(values)

    if n < 3:
        return _empty_result(request.metric_name, request.method, n, request.forecast_steps, "历史数据不足，至少需要 3 个点")

    # 解析时间间隔
    interval = timedelta(minutes=request.interval_minutes)

    # 根据方法选择预测逻辑
    if request.method == PredictionMethod.linear:
        predictions = _predict_linear(values, timestamps, request.forecast_steps, interval)
    elif request.method == PredictionMethod.moving_average:
        predictions = _predict_moving_average(values, timestamps, request.forecast_steps, interval)
    elif request.method == PredictionMethod.exponential_smoothing:
        predictions = _predict_exponential_smoothing(values, timestamps, request.forecast_steps, interval)
    else:
        predictions = _predict_linear(values, timestamps, request.forecast_steps, interval)

    # 计算趋势方向与强度
    trend_direction, trend_strength = _compute_trend(values, predictions)

    # 生成摘要
    summary = _generate_summary(
        request.metric_name,
        trend_direction,
        trend_strength,
        request.forecast_steps,
        request.method,
    )

    return TrendPredictData(
        metric_name=request.metric_name,
        method=request.method,
        historical_count=n,
        forecast_steps=request.forecast_steps,
        predictions=predictions,
        trend_direction=trend_direction,
        trend_strength=round(trend_strength, 4),
        summary=summary,
    )


def _predict_linear(
    values: list[float],
    timestamps: list[str],
    steps: int,
    interval: timedelta,
) -> list[PredictedPoint]:
    """线性回归预测。"""
    n = len(values)
    # x 取 0, 1, 2, ...
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n

    numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    slope = numerator / denominator if denominator != 0 else 0.0
    intercept = y_mean - slope * x_mean

    # 计算残差标准差用于置信区间
    residuals = [values[i] - (intercept + slope * i) for i in range(n)]
    mse = sum(r ** 2 for r in residuals) / n if n > 0 else 0.0
    residual_std = math.sqrt(mse) if mse > 0 else 0.0

    # 解析最后一个时间戳
    last_ts = _parse_timestamp(timestamps[-1])

    predictions: list[PredictedPoint] = []
    for step in range(1, steps + 1):
        x_future = n - 1 + step
        predicted = intercept + slope * x_future
        # 置信区间随步数扩大
        margin = 1.96 * residual_std * math.sqrt(1 + 1 / n + (x_future - x_mean) ** 2 / denominator) if denominator != 0 else 1.96 * residual_std
        future_ts = last_ts + interval * step

        predictions.append(
            PredictedPoint(
                timestamp=future_ts.isoformat(),
                predicted_value=round(predicted, 4),
                lower_bound=round(predicted - margin, 4) if margin > 0 else None,
                upper_bound=round(predicted + margin, 4) if margin > 0 else None,
                confidence=round(max(0.5, 1.0 - step * 0.05), 4),
            )
        )

    return predictions


def _predict_moving_average(
    values: list[float],
    timestamps: list[str],
    steps: int,
    interval: timedelta,
) -> list[PredictedPoint]:
    """移动平均预测（使用最近窗口）。"""
    n = len(values)
    window = min(5, n)  # 默认窗口为 5 或数据长度
    recent_avg = sum(values[-window:]) / window

    # 计算历史波动用于置信区间
    variance = sum((v - recent_avg) ** 2 for v in values[-window:]) / window
    std = math.sqrt(variance) if variance > 0 else 0.0

    last_ts = _parse_timestamp(timestamps[-1])

    predictions: list[PredictedPoint] = []
    for step in range(1, steps + 1):
        margin = 1.5 * std * math.sqrt(step)  # 随步数扩大
        future_ts = last_ts + interval * step

        predictions.append(
            PredictedPoint(
                timestamp=future_ts.isoformat(),
                predicted_value=round(recent_avg, 4),
                lower_bound=round(recent_avg - margin, 4) if margin > 0 else None,
                upper_bound=round(recent_avg + margin, 4) if margin > 0 else None,
                confidence=round(max(0.5, 1.0 - step * 0.08), 4),
            )
        )

    return predictions


def _predict_exponential_smoothing(
    values: list[float],
    timestamps: list[str],
    steps: int,
    interval: timedelta,
) -> list[PredictedPoint]:
    """一次指数平滑预测。"""
    n = len(values)
    alpha = 0.3  # 平滑系数

    # 初始化
    smoothed = values[0]
    for i in range(1, n):
        smoothed = alpha * values[i] + (1 - alpha) * smoothed

    # 计算历史误差
    errors = [abs(values[i] - values[i - 1]) for i in range(1, n)]
    mean_error = sum(errors) / len(errors) if errors else 0.0

    last_ts = _parse_timestamp(timestamps[-1])

    predictions: list[PredictedPoint] = []
    for step in range(1, steps + 1):
        margin = 1.5 * mean_error * math.sqrt(step)
        future_ts = last_ts + interval * step

        predictions.append(
            PredictedPoint(
                timestamp=future_ts.isoformat(),
                predicted_value=round(smoothed, 4),
                lower_bound=round(smoothed - margin, 4) if margin > 0 else None,
                upper_bound=round(smoothed + margin, 4) if margin > 0 else None,
                confidence=round(max(0.5, 1.0 - step * 0.06), 4),
            )
        )

    return predictions


def _parse_timestamp(ts_str: str) -> datetime:
    """解析 ISO 8601 时间戳。"""
    try:
        # 尝试直接解析
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        # 回退到当前时间
        return datetime.now(UTC)


def _compute_trend(values: list[float], predictions: list[PredictedPoint]) -> tuple[str, float]:
    """计算趋势方向与强度。

    Returns:
        (direction, strength) — direction 为 up/down/stable，strength 为 0~1
    """
    if not predictions:
        return "stable", 0.0

    historical_avg = sum(values) / len(values) if values else 0.0
    predicted_avg = sum(p.predicted_value for p in predictions) / len(predictions)

    if historical_avg == 0:
        return "stable", 0.0

    change_ratio = abs(predicted_avg - historical_avg) / historical_avg

    if change_ratio < 0.05:
        return "stable", round(change_ratio / 0.05, 4)
    elif predicted_avg > historical_avg:
        return "up", round(min(change_ratio, 1.0), 4)
    else:
        return "down", round(min(change_ratio, 1.0), 4)


def _empty_result(
    metric_name: str,
    method: PredictionMethod,
    historical_count: int,
    forecast_steps: int,
    reason: str,
) -> TrendPredictData:
    """生成空结果（数据不足时）。"""
    return TrendPredictData(
        metric_name=metric_name,
        method=method,
        historical_count=historical_count,
        forecast_steps=forecast_steps,
        predictions=[],
        trend_direction="unknown",
        trend_strength=0.0,
        summary=f"预测失败：{reason}",
    )


def _generate_summary(
    metric_name: str,
    direction: str,
    strength: float,
    steps: int,
    method: PredictionMethod,
) -> str:
    """生成预测结论摘要。"""
    direction_text = {"up": "上升", "down": "下降", "stable": "平稳"}.get(direction, "未知")
    strength_text = "微弱" if strength < 0.3 else "明显" if strength < 0.7 else "强烈"

    return f"{metric_name} 未来 {steps} 个周期呈 {strength_text}{direction_text}趋势（方法：{method.value}，强度：{strength:.2f}）"
