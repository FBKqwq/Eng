"""日志模式分析服务。

提供日志模式识别、模板提取、异常模式检测等功能。
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.log_analysis import (
    LogEntry,
    LogPattern,
    LogPatternAnalysis,
    PatternMatch,
)


def analyze_log_patterns(logs: List[LogEntry], top_n: int = 10) -> LogPatternAnalysis:
    """分析日志模式，提取常见模板。

    Args:
        logs: 日志条目列表
        top_n: 返回前N个最常见的模式

    Returns:
        LogPatternAnalysis: 模式分析结果
    """
    if not logs:
        return LogPatternAnalysis(
            total_logs=0,
            unique_patterns=0,
            patterns=[],
            summary="无日志数据"
        )

    # 提取所有日志的模式
    pattern_map: Dict[str, List[LogEntry]] = {}
    
    for log in logs:
        pattern = _extract_pattern(log.message)
        if pattern not in pattern_map:
            pattern_map[pattern] = []
        pattern_map[pattern].append(log)

    # 按出现次数排序
    sorted_patterns = sorted(
        pattern_map.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )[:top_n]

    # 构建结果
    patterns: List[LogPattern] = []
    total_matched = 0

    for pattern_str, matched_logs in sorted_patterns:
        count = len(matched_logs)
        total_matched += count
        
        # 提取示例
        examples = [
            matched_logs[i].message 
            for i in range(min(3, len(matched_logs)))
        ]
        
        # 计算严重级别分布
        severity_counts = Counter(log.level for log in matched_logs)
        
        patterns.append(LogPattern(
            pattern=pattern_str,
            count=count,
            percentage=(count / len(logs)) * 100,
            examples=examples,
            severity_distribution=dict(severity_counts)
        ))

    summary = f"共分析 {len(logs)} 条日志，识别出 {len(pattern_map)} 种模式，展示前 {len(patterns)} 种"

    return LogPatternAnalysis(
        total_logs=len(logs),
        unique_patterns=len(pattern_map),
        patterns=patterns,
        summary=summary
    )


def detect_anomaly_patterns(logs: List[LogEntry], threshold: float = 0.05) -> List[PatternMatch]:
    """检测异常日志模式（出现频率极低的模式）。

    Args:
        logs: 日志条目列表
        threshold: 异常阈值，低于此百分比的模式视为异常

    Returns:
        List[PatternMatch]: 异常模式列表
    """
    if not logs:
        return []

    # 提取模式并统计
    pattern_map: Dict[str, List[LogEntry]] = {}
    for log in logs:
        pattern = _extract_pattern(log.message)
        if pattern not in pattern_map:
            pattern_map[pattern] = []
        pattern_map[pattern].append(log)

    # 识别异常模式
    anomalies: List[PatternMatch] = []
    
    for pattern, matched_logs in pattern_map.items():
        percentage = (len(matched_logs) / len(logs)) * 100
        if percentage < threshold:
            # 获取第一个匹配的日志作为示例
            sample_log = matched_logs[0]
            anomalies.append(PatternMatch(
                pattern=pattern,
                count=len(matched_logs),
                percentage=percentage,
                first_occurrence=sample_log.timestamp,
                level=sample_log.level,
                message=sample_log.message
            ))

    # 按出现次数排序（最少的在前）
    anomalies.sort(key=lambda x: x.count)
    
    return anomalies


def _extract_pattern(message: str) -> str:
    """从日志消息中提取模式模板。

    将数字、IP地址、UUID等动态内容替换为占位符。

    Args:
        message: 日志消息

    Returns:
        str: 模式模板
    """
    pattern = message
    
    # 替换IP地址
    pattern = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP]', pattern)
    
    # 替换端口号
    pattern = re.sub(r':\d{1,5}\b', ':[PORT]', pattern)
    
    # 替换数字序列
    pattern = re.sub(r'\b\d{4,}\b', '[NUM]', pattern)
    
    # 替换UUID
    pattern = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '[UUID]', pattern, flags=re.IGNORECASE)
    
    # 替换时间戳
    pattern = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?', '[TIME]', pattern)
    
    # 替换十六进制
    pattern = re.sub(r'0x[0-9a-f]+', '[HEX]', pattern, flags=re.IGNORECASE)
    
    # 替换路径
    pattern = re.sub(r'(/[\w.-]+)+', '[PATH]', pattern)
    
    # 替换请求ID/TraceID
    pattern = re.sub(r'(request_id|trace_id|span_id)=[\w-]+', r'\1=[ID]', pattern, flags=re.IGNORECASE)
    
    # 替换任意单词（作为最后的兜底）
    pattern = re.sub(r'\b[a-zA-Z0-9]{16,}\b', '[TOKEN]', pattern)
    
    return pattern
