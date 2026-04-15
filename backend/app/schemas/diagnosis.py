from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

"""
负责规定：智能诊断系统的输入输出格式，一次诊断长什么样，怎么进，怎么出，过程怎么表示
定义了“诊断请求”、“规则引擎的输出”，“诊断证据结构”、“最终结果”
"""

# =========================
# Enums 值字段定义
# =========================

class AnomalyType(str, Enum):
    api_timeout = "api_timeout"
    database_exception = "database_exception"
    redis_exception = "redis_exception"
    payment_exception = "payment_exception"
    inventory_exception = "inventory_exception"
    recommendation_exception = "recommendation_exception"
    search_exception = "search_exception"
    login_security_exception = "login_security_exception"
    risk_control_exception = "risk_control_exception"
    infrastructure_exception = "infrastructure_exception"
    unknown_exception = "unknown_exception"


class SeverityLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class DiagnosisSource(str, Enum):
    rule_engine = "rule_engine"
    llm = "llm"
    langgraph = "langgraph"
    hybrid = "hybrid"


class DiagnosisStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    reviewed = "reviewed"
    closed = "closed"


class RoutingDecision(str, Enum):
    direct_rule = "direct_rule"
    rule_then_llm = "rule_then_llm"
    full_llm = "full_llm"
    rejected = "rejected"


class NodeStatus(str, Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"
    skipped = "skipped"


class ReviewStatus(str, Enum):
    unreviewed = "unreviewed"
    confirmed = "confirmed"
    rejected = "rejected"
    adjusted = "adjusted"


class SuggestionPriority(str, Enum):
    p0 = "P0"
    p1 = "P1"
    p2 = "P2"
    p3 = "P3"


class SuggestionCategory(str, Enum):
    immediate_action = "immediate_action"
    troubleshooting = "troubleshooting"
    mitigation = "mitigation"
    optimization = "optimization"
    observation = "observation"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


# =========================
# Request Models 请求体模型
# =========================

class DiagnosisRequest(BaseModel):
    request_id: str = Field(..., description="诊断请求ID")
    anchor_log_id: Optional[str] = Field(default=None, description="锚点日志ID")
    trace_id: Optional[str] = Field(default=None, description="调用链ID")
    service_name: Optional[str] = Field(default=None, description="目标服务名")
    error_code: Optional[str] = Field(default=None, description="目标错误码")
    time_range_start: Optional[datetime] = Field(default=None, description="时间范围起点")
    time_range_end: Optional[datetime] = Field(default=None, description="时间范围终点")
    include_context_logs: bool = Field(default=True, description="是否包含上下文日志")
    include_metrics_summary: bool = Field(default=True, description="是否包含指标摘要")
    include_related_errors: bool = Field(default=True, description="是否包含关联错误")
    max_logs: int = Field(default=100, description="最大日志条数")
    force_llm: bool = Field(default=False, description="是否强制进入LLM流程")
    preferred_anomaly_types: Optional[List[AnomalyType]] = Field(default=None, description="优先异常类别")
    operator: Optional[str] = Field(default=None, description="发起人")
    remark: Optional[str] = Field(default=None, description="备注")

    @field_validator("max_logs")
    @classmethod
    def validate_max_logs(cls, v: int) -> int:
        if v < 1 or v > 1000:
            raise ValueError("max_logs 必须在 1~1000 之间")
        return v


class BatchDiagnosisRequest(BaseModel):
    request_ids: List[str] = Field(default_factory=list, description="批量请求ID列表")
    anchor_log_ids: List[str] = Field(default_factory=list, description="锚点日志ID列表")
    force_llm: bool = Field(default=False, description="是否强制LLM")
    max_batch_size: int = Field(default=20, description="批量上限")


class DiagnosisQueryRequest(BaseModel):
    anomaly_types: Optional[List[AnomalyType]] = None
    severity_levels: Optional[List[SeverityLevel]] = None
    service_names: Optional[List[str]] = None
    sources: Optional[List[DiagnosisSource]] = None
    statuses: Optional[List[DiagnosisStatus]] = None
    review_statuses: Optional[List[ReviewStatus]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = 1
    page_size: int = 20
    sort_by: str = "created_at"
    sort_order: SortOrder = SortOrder.desc

    @field_validator("page")
    @classmethod
    def validate_page(cls, v: int) -> int:
        if v < 1:
            raise ValueError("page 必须 >= 1")
        return v

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, v: int) -> int:
        if v < 1 or v > 200:
            raise ValueError("page_size 必须在 1~200 之间")
        return v


# =========================
# Rule Routing Models 规则路由模型
# =========================

class RuleHit(BaseModel):
    rule_id: str
    rule_name: str
    rule_version: Optional[str] = None
    matched: bool = True
    score: float = 0.0
    reason: Optional[str] = None
    matched_fields: List[str] = Field(default_factory=list)
    suggested_anomaly_type: Optional[AnomalyType] = None
    suggested_severity: Optional[SeverityLevel] = None


class RoutingResult(BaseModel):
    decision: RoutingDecision
    final_source: DiagnosisSource
    confidence: float = 0.0
    rule_hits: List[RuleHit] = Field(default_factory=list)
    reason: Optional[str] = None
    should_fetch_context: bool = True
    should_call_llm: bool = False
    should_short_circuit: bool = False


# =========================
# Context / Evidence Models 上下文/证据模型
# =========================

class EvidenceLog(BaseModel):
    log_id: str
    timestamp: datetime
    service_name: str
    log_level: str
    event_type: str
    message: str
    error_code: Optional[str] = None
    trace_id: Optional[str] = None
    score: float = 0.0
    reason: Optional[str] = None
    snippet: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class ContextSummary(BaseModel):
    trace_id: Optional[str] = None
    related_services: List[str] = Field(default_factory=list)
    related_error_codes: List[str] = Field(default_factory=list)
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    total_logs: int = 0
    error_log_count: int = 0
    warning_log_count: int = 0
    top_error_codes: List[str] = Field(default_factory=list)
    top_services: List[str] = Field(default_factory=list)
    summary_text: Optional[str] = None


class MetricsSummary(BaseModel):
    service_name: Optional[str] = None
    window_minutes: Optional[int] = None
    avg_response_time_ms: Optional[float] = None
    p95_response_time_ms: Optional[float] = None
    p99_response_time_ms: Optional[float] = None
    error_rate: Optional[float] = None
    timeout_rate: Optional[float] = None
    qps: Optional[float] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    db_avg_duration_ms: Optional[float] = None
    redis_hit_rate: Optional[float] = None


# =========================
# Workflow / Node Models LangGraph工作流节点
# =========================

class DiagnosisNodeResult(BaseModel):
    node_name: str
    status: NodeStatus
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    error_message: Optional[str] = None


class DiagnosisWorkflowState(BaseModel):
    workflow_id: str
    status: DiagnosisStatus
    current_node: Optional[str] = None
    completed_nodes: List[str] = Field(default_factory=list)
    failed_node: Optional[str] = None
    node_results: List[DiagnosisNodeResult] = Field(default_factory=list)


# =========================
# Result Models 最终业务结果模型
# =========================

class RootCauseCandidate(BaseModel):
    rank: int
    cause: str
    confidence: float
    reason: Optional[str] = None
    related_services: List[str] = Field(default_factory=list)
    related_error_codes: List[str] = Field(default_factory=list)


class ActionSuggestion(BaseModel):
    title: str
    detail: str
    priority: SuggestionPriority
    category: SuggestionCategory
    is_immediate: bool = False


class DiagnosisResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    diagnosis_id: str
    request_id: str
    status: DiagnosisStatus
    source: DiagnosisSource
    anomaly_type: AnomalyType
    severity: SeverityLevel
    title: str
    summary: str
    root_cause: str
    root_cause_candidates: List[RootCauseCandidate] = Field(default_factory=list)
    affected_services: List[str] = Field(default_factory=list)
    affected_time_range_start: Optional[datetime] = None
    affected_time_range_end: Optional[datetime] = None
    evidence_logs: List[EvidenceLog] = Field(default_factory=list)
    action_suggestions: List[ActionSuggestion] = Field(default_factory=list)
    confidence: float = 0.0
    routing_result: Optional[RoutingResult] = None
    context_summary: Optional[ContextSummary] = None
    metrics_summary: Optional[MetricsSummary] = None
    workflow_state: Optional[DiagnosisWorkflowState] = None
    review_status: ReviewStatus = ReviewStatus.unreviewed
    review_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DiagnosisListItem(BaseModel):
    diagnosis_id: str
    anomaly_type: AnomalyType
    severity: SeverityLevel
    source: DiagnosisSource
    service_names: List[str] = Field(default_factory=list)
    summary: str
    confidence: float = 0.0
    status: DiagnosisStatus
    review_status: ReviewStatus = ReviewStatus.unreviewed
    created_at: datetime


class DiagnosisPageResponse(BaseModel):
    items: List[DiagnosisListItem]
    total: int
    page: int
    page_size: int
    has_more: bool