"""时序异常检测服务。

职责：基于统计方法（Z-Score、IQR、MAD）对时序数据进行异常检测，
不依赖外部 ML 库，纯 Python 实现，保证轻量与可维护性。
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

from app.schemas.prediction import (
    AnomalyDetectData,
    AnomalyDetectRequest,
    AnomalyLevel,
    AnomalyMethod,
    AnomalyPoint,
)


def detect_anomalies(request: AnomalyDetectRequest) -> AnomalyDetectData:
    """执行时序异常检测。

    根据 request.method 选择检测算法：
    - zscore: 标准差法，适合近似正态分布的数据
    - iqr: 四分位距法，对异常值鲁棒
    - mad: 绝对中位差法，对极端异常值鲁棒
    """
    values = [p.value for p in request.data]
    timestamps = [p.timestamp for p in request.data]
    n = len(values)

    if n < 3:
        return _empty_result(request.metric_name, request.method, n, "数据点不足，至少需要 3 个点")

    # 根据方法选择检测逻辑
    if request.method == AnomalyMethod.zscore:
        anomalies = _detect_zscore(values, timestamps, request.threshold, request.sensitivity)
    elif request.method == AnomalyMethod.iqr:
        anomalies = _detect_iqr(values, timestamps, request.threshold, request.sensitivity)
    elif request.method == AnomalyMethod.mad:
        anomalies = _detect_mad(values, timestamps, request.threshold, request.sensitivity)
    else:
        anomalies = _detect_zscore(values, timestamps, request.threshold, request.sensitivity)

    # 统计摘要
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    std = math.sqrt(variance) if variance > 0 else 0.0

    stats = {
        "mean": round(mean, 4),
        "std": round(std, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }

    anomaly_count = len(anomalies)
    anomaly_ratio = anomaly_count / n if n > 0 else 0.0

    # 生成摘要
    summary = _generate_summary(request.metric_name, anomaly_count, n, anomaly_ratio, request.method)

    return AnomalyDetectData(
        metric_name=request.metric_name,
        method=request.method,
        total_points=n,
        anomaly_count=anomaly_count,
        anomaly_ratio=round(anomaly_ratio, 4),
        anomalies=anomalies,
        stats=stats,
        summary=summary,
    )


def _detect_zscore(
    values: list[float],
    timestamps: list[str],
    threshold: float,
    sensitivity: float,
) -> list[AnomalyPoint]:
    """Z-Score 异常检测。"""
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    std = math.sqrt(variance) if variance > 0 else 1e-9

    effective_threshold = threshold / sensitivity
    anomalies: list[AnomalyPoint] = []

    for i, (ts, val) in enumerate(zip(timestamps, values)):
        zscore = abs(val - mean) / std
        if zscore > effective_threshold:
            level = _level_by_deviation(zscore, effective_threshold)
            anomalies.append(
                AnomalyPoint(
                    timestamp=ts,
                    value=round(val, 4),
                    expected=round(mean, 4),
                    deviation=round(zscore, 4),
                    level=level,
                    reason=f"Z-Score={zscore:.2f} > 阈值 {effective_threshold:.2f}",
                )
            )

    return anomalies


def _detect_iqr(
    values: list[float],
    timestamps: list[str],
    threshold: float,
    sensitivity: float,
) -> list[AnomalyPoint]:
    """IQR（四分位距）异常检测。"""
    sorted_values = sorted(values)
    n = len(sorted_values)

    q1_idx = (n - 1) * 0.25
    q3_idx = (n - 1) * 0.75
    q1 = _interpolate(sorted_values, q1_idx)
    q3 = _interpolate(sorted_values, q3_idx)
    iqr = q3 - q1 if q3 > q1 else 1e-9

    effective_threshold = threshold / sensitivity
    lower_bound = q1 - effective_threshold * iqr
    upper_bound = q3 + effective_threshold * iqr

    anomalies: list[AnomalyPoint] = []
    median = sorted_values[n // 2] if n % 2 == 1 else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2

    for ts, val in zip(timestamps, values):
        if val < lower_bound or val > upper_bound:
            deviation = abs(val - median) / iqr if iqr > 0 else 0.0
            level = _level_by_deviation(deviation, effective_threshold)
            direction = "偏低" if val < lower_bound else "偏高"
            anomalies.append(
                AnomalyPoint(
                    timestamp=ts,
                    value=round(val, 4),
                    expected=round(median, 4),
                    deviation=round(deviation, 4),
                    level=level,
                    reason=f"{direction}：{val:.2f} 超出 IQR 边界 [{lower_bound:.2f}, {upper_bound:.2f}]",
                )
            )

    return anomalies


def _detect_mad(
    values: list[float],
    timestamps: list[str],
    threshold: float,
    sensitivity: float,
) -> list[AnomalyPoint]:
    """MAD（绝对中位差）异常检测。"""
    sorted_values = sorted(values)
    n = len(sorted_values)
    median = sorted_values[n // 2] if n % 2 == 1 else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2

    abs_deviations = [abs(v - median) for v in values]
    sorted_abs_dev = sorted(abs_deviations)
    mad = sorted_abs_dev[n // 2] if n % 2 == 1 else (sorted_abs_dev[n // 2 - 1] + sorted_abs_dev[n // 2]) / 2
    mad = mad if mad > 0 else 1e-9

    effective_threshold = threshold / sensitivity
    anomalies: list[AnomalyPoint] = []

    for ts, val in zip(timestamps, values):
        modified_z = 0.6745 * (val - median) / mad
        if abs(modified_z) > effective_threshold:
            deviation = abs(modified_z)
            level = _level_by_deviation(deviation, effective_threshold)
            direction = "偏低" if modified_z < 0 else "偏高"
            anomalies.append(
                AnomalyPoint(
                    timestamp=ts,
                    value=round(val, 4),
                    expected=round(median, 4),
                    deviation=round(deviation, 4),
                    level=level,
                    reason=f"{direction}：Modified Z-Score={abs(modified_z):.2f} > 阈值 {effective_threshold:.2f}",
                )
            )

    return anomalies


def _interpolate(sorted_values: list[float], idx: float) -> float:
    """线性插值获取分位数。"""
    lower = int(math.floor(idx))
    upper = int(math.ceil(idx))
    if lower == upper:
        return sorted_values[lower]
    frac = idx - lower
    return sorted_values[lower] * (1 - frac) + sorted_values[upper] * frac


def _level_by_deviation(deviation: float, threshold: float) -> AnomalyLevel:
    """根据偏离程度判定异常等级。"""
    ratio = deviation / threshold if threshold > 0 else 0.0
    if ratio > 2.0:
        return AnomalyLevel.critical
    elif ratio > 1.5:
        return AnomalyLevel.warning
    return AnomalyLevel.normal


def _empty_result(metric_name: str, method: AnomalyMethod, total_points: int, reason: str) -> AnomalyDetectData:
    """生成空结果（数据不足时）。"""
    return AnomalyDetectData(
        metric_name=metric_name,
        method=method,
        total_points=total_points,
        anomaly_count=0,
        anomaly_ratio=0.0,
        anomalies=[],
        stats={},
        summary=f"检测失败：{reason}",
    )


def _generate_summary(
    metric_name: str,
    anomaly_count: int,
    total: int,
    ratio: float,
    method: AnomalyMethod,
) -> str:
    """生成检测结论摘要。"""
    if anomaly_count == 0:
        return f"{metric_name} 在 {total} 个数据点中未检测到异常（方法：{method.value}）"
    if ratio > 0.3:
        return f"{metric_name} 检测到 {anomaly_count}/{total} 个异常点（占比 {ratio:.1%}），异常频率较高，建议排查系统性问题"
    elif ratio > 0.1:
        return f"{metric_name} 检测到 {anomaly_count}/{total} 个异常点（占比 {ratio:.1%}），存在间歇性异常"
    return f"{metric_name} 检测到 {anomaly_count}/{total} 个异常点（占比 {ratio:.1%}），偶发性异常"
