"""日志聚类分析服务。

提供基于文本相似度的日志聚类功能，帮助发现日志中的模式组。
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

from app.schemas.log_analysis import (
    ClusterResult,
    LogCluster,
    LogEntry,
)


def cluster_logs(logs: List[LogEntry], max_clusters: int = 10, similarity_threshold: float = 0.6) -> ClusterResult:
    """对日志进行聚类分析。

    Args:
        logs: 日志条目列表
        max_clusters: 最大聚类数量
        similarity_threshold: 相似度阈值

    Returns:
        ClusterResult: 聚类结果
    """
    if not logs:
        return ClusterResult(
            total_clusters=0,
            total_logs=0,
            clusters=[],
            summary="无日志数据"
        )

    # 简单的基于模式的聚类
    clusters: List[LogCluster] = []
    pattern_to_cluster: Dict[str, int] = {}

    for log in logs:
        pattern = _simplify_pattern(log.message)
        
        if pattern in pattern_to_cluster:
            # 添加到已有聚类
            cluster_idx = pattern_to_cluster[pattern]
            clusters[cluster_idx].logs.append(log)
            clusters[cluster_idx].count += 1
        else:
            # 创建新聚类（不超过最大数量）
            if len(clusters) < max_clusters:
                severity_counts = Counter()
                severity_counts[log.level] += 1
                
                clusters.append(LogCluster(
                    cluster_id=f"cluster_{len(clusters) + 1}",
                    pattern=pattern,
                    count=1,
                    logs=[log],
                    severity_distribution=dict(severity_counts),
                    representative=log.message
                ))
                pattern_to_cluster[pattern] = len(clusters) - 1

    # 按大小排序
    clusters.sort(key=lambda x: x.count, reverse=True)

    # 计算统计信息
    total_logs = sum(c.count for c in clusters)
    avg_cluster_size = total_logs / len(clusters) if clusters else 0

    summary = f"共 {len(clusters)} 个聚类，平均每个聚类 {avg_cluster_size:.1f} 条日志"

    return ClusterResult(
        total_clusters=len(clusters),
        total_logs=total_logs,
        clusters=clusters,
        summary=summary
    )


def get_cluster_summary(clusters: List[LogCluster]) -> Dict[str, Any]:
    """获取聚类统计摘要。

    Args:
        clusters: 聚类列表

    Returns:
        Dict[str, Any]: 统计摘要
    """
    if not clusters:
        return {
            "total_clusters": 0,
            "total_logs": 0,
            "largest_cluster_size": 0,
            "smallest_cluster_size": 0,
            "avg_cluster_size": 0,
            "severity_distribution": {}
        }

    total_logs = sum(c.count for c in clusters)
    sizes = [c.count for c in clusters]
    
    # 统计严重级别分布
    severity_dist = Counter()
    for cluster in clusters:
        for level, count in cluster.severity_distribution.items():
            severity_dist[level] += count

    return {
        "total_clusters": len(clusters),
        "total_logs": total_logs,
        "largest_cluster_size": max(sizes),
        "smallest_cluster_size": min(sizes),
        "avg_cluster_size": total_logs / len(clusters),
        "severity_distribution": dict(severity_dist)
    }


def _simplify_pattern(message: str) -> str:
    """简化日志消息为模式。

    保留关键词，移除变量部分。
    """
    import re
    
    # 移除数字和特殊字符
    pattern = re.sub(r'\d+', '[NUM]', message)
    pattern = re.sub(r'[^\w\s]', '', pattern)
    
    # 转换为小写并分词
    words = pattern.lower().split()
    
    # 保留有意义的关键词（过滤常见词）
    stop_words = {'the', 'and', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                  'could', 'should', 'may', 'might', 'must', 'shall', 'can',
                  'need', 'dare', 'ought', 'used', 'to', 'of', 'in', 'for',
                  'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
                  'during', 'before', 'after', 'above', 'below', 'between',
                  'under', 'again', 'further', 'then', 'once', 'here', 'there',
                  'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more',
                  'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
                  'own', 'same', 'so', 'than', 'too', 'very', 'just', 'or'}
    
    # 保留至少3个字符的非停用词
    keywords = [word for word in words if len(word) >= 3 and word not in stop_words]
    
    # 如果关键词太少，保留原始模式的前几个词
    if len(keywords) < 3:
        keywords = words[:5]
    
    return ' '.join(keywords)
