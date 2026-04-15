from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, ConfigDict, field_validator

"""
负责规定：一条日志长什么样，怎么查，怎么回
日志分为六大类：
    “行为日志
    应用日志
    性能日志
    安全日志
    基础设施日志
    审计日志“
每类日志除了公共字段，还有：”
    行为日志：
        用户是谁
        看了什么商品
        搜了什么词
        是否加入购物车
        是否支付尝试
    应用日志：
        哪个接口
        响应码
        响应耗时
        错误码
        下游服务
        数据库耗时
        Redis 命中情况
    安全日志：
        风险等级
        命中了什么规则
        是否非法 token
        是否高频访问
    “
定义了日志查询的传参与返回结构
"""

# =========================
# Enums 值字段定义
# =========================

class LogLevel(str, Enum):
    debug = "DEBUG"
    info = "INFO"
    warning = "WARNING"
    error = "ERROR"
    critical = "CRITICAL"


class LogType(str, Enum):
    behavior = "behavior"
    application = "application"
    performance = "performance"
    security = "security"
    infrastructure = "infrastructure"
    audit = "audit"


class Environment(str, Enum):
    dev = "dev"
    test = "test"
    prod = "prod"


class EventStatus(str, Enum):
    success = "success"
    fail = "fail"
    timeout = "timeout"
    blocked = "blocked"
    partial_success = "partial_success"
    unknown = "unknown"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class BehaviorAction(str, Enum):
    view_product = "view_product"
    search_keyword = "search_keyword"
    click_recommendation = "click_recommendation"
    add_to_cart = "add_to_cart"
    submit_order = "submit_order"
    payment_attempt = "payment_attempt"


class ApplicationAction(str, Enum):
    api_request = "api_request"
    service_call = "service_call"
    db_query = "db_query"
    redis_access = "redis_access"
    inventory_check = "inventory_check"
    payment_gateway_call = "payment_gateway_call"
    recommendation_call = "recommendation_call"
    sort_call = "sort_call"
    exception = "exception"


class PerformanceMetric(str, Enum):
    response_time = "response_time"
    db_duration = "db_duration"
    redis_duration = "redis_duration"
    qps = "qps"
    tps = "tps"
    kafka_produce_rate = "kafka_produce_rate"
    kafka_consume_rate = "kafka_consume_rate"
    es_index_rate = "es_index_rate"
    es_query_latency = "es_query_latency"
    cpu_percent = "cpu_percent"
    memory_percent = "memory_percent"
    disk_percent = "disk_percent"


class SecurityAction(str, Enum):
    login_failed = "login_failed"
    illegal_token = "illegal_token"
    high_frequency_ip_access = "high_frequency_ip_access"
    burst_ordering = "burst_ordering"
    crawler_access = "crawler_access"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class InfrastructureComponent(str, Enum):
    host = "host"
    docker = "docker"
    kafka = "kafka"
    elasticsearch = "elasticsearch"
    kibana = "kibana"
    logstash = "logstash"
    backend = "backend"


class ResourceType(str, Enum):
    cpu = "cpu"
    memory = "memory"
    disk = "disk"
    network = "network"
    topic = "topic"
    index = "index"
    cluster = "cluster"


class InfrastructureSeverity(str, Enum):
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class AuditAction(str, Enum):
    admin_operation = "admin_operation"
    config_change = "config_change"
    manual_reissue_order = "manual_reissue_order"
    manual_refund = "manual_refund"
    permission_change = "permission_change"


class AggregateField(str, Enum):
    log_level = "log_level"
    service_name = "service_name"
    log_type = "log_type"
    event_type = "event_type"
    error_code = "error_code"
    status_code = "status_code"
    user_id = "user_id"
    client_ip = "client_ip"


class TimeInterval(str, Enum):
    minute = "1m"
    hour = "1h"
    day = "1d"


# =========================
# Base / Common 基础公共字段
# =========================

class LogBase(BaseModel):
    model_config = ConfigDict(extra="allow")

    timestamp: datetime = Field(..., description="日志发生时间")
    log_id: str = Field(..., description="日志唯一ID")
    log_level: LogLevel = Field(..., description="日志级别")
    log_type: LogType = Field(..., description="日志大类")
    event_type: str = Field(..., description="事件类型")
    service_name: str = Field(..., description="服务名称")
    service_instance: Optional[str] = Field(default=None, description="服务实例")
    host: Optional[str] = Field(default=None, description="主机名或容器宿主机")
    env: Environment = Field(default=Environment.dev, description="运行环境")
    message: str = Field(..., description="日志消息")
    source_type: Optional[str] = Field(default=None, description="来源类型")
    trace_id: Optional[str] = Field(default=None, description="链路追踪ID")
    span_id: Optional[str] = Field(default=None, description="Span ID")
    request_id: Optional[str] = Field(default=None, description="请求ID")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    session_id: Optional[str] = Field(default=None, description="会话ID")
    client_ip: Optional[str] = Field(default=None, description="客户端IP")
    user_agent: Optional[str] = Field(default=None, description="UA")
    status: Optional[EventStatus] = Field(default=EventStatus.unknown, description="事件状态")
    tags: List[str] = Field(default_factory=list, description="标签")
    extra: Dict[str, Any] = Field(default_factory=dict, description="扩展字段")


# =========================
# Domain Logs 业务域日志模型
# =========================

class BehaviorLog(LogBase):
    log_type: Literal[LogType.behavior] = LogType.behavior

    action: BehaviorAction
    page: Optional[str] = None
    module: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    category_id: Optional[str] = None
    cart_id: Optional[str] = None
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    recommendation_id: Optional[str] = None
    strategy_id: Optional[str] = None
    keyword: Optional[str] = None
    result_count: Optional[int] = None
    position: Optional[int] = None
    quantity: Optional[int] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    is_success: Optional[bool] = None


class ApplicationLog(LogBase):
    log_type: Literal[LogType.application] = LogType.application

    action: ApplicationAction
    request_path: Optional[str] = None
    http_method: Optional[HttpMethod] = None
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    error_code: Optional[str] = None
    exception_type: Optional[str] = None
    upstream_service: Optional[str] = None
    downstream_service: Optional[str] = None
    interface_name: Optional[str] = None
    db_operation: Optional[str] = None
    db_table: Optional[str] = None
    db_duration_ms: Optional[int] = None
    redis_operation: Optional[str] = None
    cache_key: Optional[str] = None
    cache_hit: Optional[bool] = None
    retry_count: Optional[int] = None
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    inventory_id: Optional[str] = None


class PerformanceLog(LogBase):
    log_type: Literal[LogType.performance] = LogType.performance

    metric_name: PerformanceMetric
    metric_value: float
    metric_unit: str
    window_seconds: Optional[int] = None
    qps: Optional[float] = None
    tps: Optional[float] = None
    p50_ms: Optional[float] = None
    p95_ms: Optional[float] = None
    p99_ms: Optional[float] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_percent: Optional[float] = None
    network_in_bytes: Optional[int] = None
    network_out_bytes: Optional[int] = None
    thread_pool_active: Optional[int] = None
    connection_pool_in_use: Optional[int] = None


class SecurityLog(LogBase):
    log_type: Literal[LogType.security] = LogType.security

    action: SecurityAction
    risk_level: RiskLevel
    reason: Optional[str] = None
    token_id: Optional[str] = None
    is_token_valid: Optional[bool] = None
    ip_access_count: Optional[int] = None
    device_id: Optional[str] = None
    geo_location: Optional[str] = None
    login_username: Optional[str] = None
    is_blocked: Optional[bool] = None
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    attack_type: Optional[str] = None
    order_count_short_window: Optional[int] = None
    crawler_score: Optional[float] = None


class InfrastructureLog(LogBase):
    log_type: Literal[LogType.infrastructure] = LogType.infrastructure

    component: InfrastructureComponent
    resource_type: ResourceType
    severity: InfrastructureSeverity
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_percent: Optional[float] = None
    disk_path: Optional[str] = None
    pod_name: Optional[str] = None
    container_id: Optional[str] = None
    node_name: Optional[str] = None
    cluster_name: Optional[str] = None
    topic_name: Optional[str] = None
    partition: Optional[int] = None
    consumer_group: Optional[str] = None
    lag: Optional[int] = None
    es_index: Optional[str] = None
    es_cluster_health: Optional[str] = None


class AuditLog(LogBase):
    log_type: Literal[LogType.audit] = LogType.audit

    action: AuditAction
    operator_id: str
    operator_name: Optional[str] = None
    operator_role: Optional[str] = None
    target_type: str
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    before_value: Optional[Dict[str, Any]] = None
    after_value: Optional[Dict[str, Any]] = None
    change_summary: Optional[str] = None
    approval_id: Optional[str] = None
    business_order_id: Optional[str] = None
    is_manual: bool = True


AnyLog = Union[
    BehaviorLog,
    ApplicationLog,
    PerformanceLog,
    SecurityLog,
    InfrastructureLog,
    AuditLog,
]


# =========================
# Query Requests 查询请求体结构
# =========================

class LogQueryRequest(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    service_names: Optional[List[str]] = None
    log_levels: Optional[List[LogLevel]] = None
    log_types: Optional[List[LogType]] = None
    event_types: Optional[List[str]] = None
    error_codes: Optional[List[str]] = None
    trace_id: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    order_id: Optional[str] = None
    keyword: Optional[str] = None
    status_codes: Optional[List[int]] = None
    statuses: Optional[List[EventStatus]] = None
    envs: Optional[List[Environment]] = None
    tags: Optional[List[str]] = None
    page: int = 1
    page_size: int = 20
    sort_by: str = "timestamp"
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
        if v < 1 or v > 500:
            raise ValueError("page_size 必须在 1~500 之间")
        return v


class LogAggregateRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    service_names: Optional[List[str]] = None
    log_types: Optional[List[LogType]] = None
    group_by: AggregateField
    interval: Optional[TimeInterval] = None
    top_n: int = 10
    filters: Optional[Dict[str, Any]] = None


class LogContextRequest(BaseModel):
    trace_id: Optional[str] = None
    request_id: Optional[str] = None
    service_name: Optional[str] = None
    anchor_log_id: Optional[str] = None
    window_minutes: int = 5
    include_same_error_code: bool = True
    include_related_services: bool = True
    limit: int = 200


# =========================
# Responses 响应结构
# =========================

class LogItem(BaseModel):
    log_id: str
    timestamp: datetime
    log_level: LogLevel
    log_type: LogType
    event_type: str
    service_name: str
    message: str
    trace_id: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    status: Optional[EventStatus] = None
    summary: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class LogPageResponse(BaseModel):
    items: List[LogItem]
    total: int
    page: int
    page_size: int
    has_more: bool
    took_ms: Optional[int] = None


class AggregateBucket(BaseModel):
    key: str
    count: int
    value: Optional[float] = None
    extra: Optional[Dict[str, Any]] = None


class LogAggregateResponse(BaseModel):
    group_by: str
    interval: Optional[str] = None
    buckets: List[AggregateBucket]
    took_ms: Optional[int] = None


class LogContextResponse(BaseModel):
    anchor: Optional[LogItem] = None
    context_logs: List[LogItem] = Field(default_factory=list)
    related_services: List[str] = Field(default_factory=list)
    related_error_codes: List[str] = Field(default_factory=list)
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None