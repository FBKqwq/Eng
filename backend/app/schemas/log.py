from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

"""
负责规定：一条日志长什么样，怎么查，怎么回
日志分为七大类：
    “行为日志
    应用日志
    Web 服务器日志
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
    Web 服务器日志：
        Nginx access/error log 标准字段
        客户端 IP、request line、状态码、响应体字节数
        referer、user agent、request_time、upstream 响应信息
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
    web_server = "web_server"
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


class HttpScheme(str, Enum):
    http = "http"
    https = "https"


class NginxLogKind(str, Enum):
    access = "access"
    error = "error"


class NginxUpstreamStatus(str, Enum):
    hit = "HIT"
    miss = "MISS"
    bypass = "BYPASS"
    expired = "EXPIRED"
    stale = "STALE"
    updating = "UPDATING"
    revalidated = "REVALIDATED"
    unavailable = "-"


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


class AggregateTemplate(str, Enum):
    """六类预置聚合模板，与 aggregation_service 及前端 metrics.js 对齐。"""

    traffic = "traffic"
    errors = "errors"
    latency = "latency"
    behavior_funnel = "behavior_funnel"
    security = "security"
    infra_health = "infra_health"


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


class WebServerLog(LogBase):
    """Nginx 风格 Web Server 日志契约，兼容 access log 与 error log。"""

    log_type: Literal[LogType.web_server] = LogType.web_server

    nginx_log_kind: NginxLogKind = Field(default=NginxLogKind.access, description="Nginx 日志类型：access 或 error")
    remote_addr: str = Field(..., description="客户端 IP，对应 Nginx $remote_addr")
    remote_user: Optional[str] = Field(default=None, description="认证用户，对应 $remote_user，未认证通常为 -")
    time_local: Optional[str] = Field(default=None, description="Nginx 原始本地时间，对应 $time_local")
    request: str = Field(..., description="完整请求行，例如 GET /api/order HTTP/1.1，对应 $request")
    request_method: HttpMethod = Field(..., description="HTTP 方法，对应 $request_method")
    request_uri: str = Field(..., description="原始请求 URI，对应 $request_uri")
    uri: Optional[str] = Field(default=None, description="规范化 URI，对应 $uri")
    query_string: Optional[str] = Field(default=None, description="查询字符串，对应 $query_string")
    server_protocol: str = Field(default="HTTP/1.1", description="协议版本，对应 $server_protocol")
    status_code: int = Field(..., ge=100, le=599, description="HTTP 响应码，对应 $status")
    body_bytes_sent: int = Field(default=0, ge=0, description="响应体字节数，对应 $body_bytes_sent")
    bytes_sent: Optional[int] = Field(default=None, ge=0, description="总发送字节数，对应 $bytes_sent")
    request_length: Optional[int] = Field(default=None, ge=0, description="请求长度，对应 $request_length")
    http_referer: Optional[str] = Field(default=None, description="来源页，对应 $http_referer")
    http_user_agent: Optional[str] = Field(default=None, description="User-Agent，对应 $http_user_agent")
    http_x_forwarded_for: Optional[str] = Field(default=None, description="代理链路客户端 IP，对应 $http_x_forwarded_for")
    host_header: Optional[str] = Field(default=None, description="Host 请求头，对应 $host")
    server_name: Optional[str] = Field(default=None, description="Nginx server_name，对应 $server_name")
    scheme: Optional[HttpScheme] = Field(default=None, description="请求协议，对应 $scheme")
    request_time: Optional[float] = Field(default=None, ge=0, description="完整请求耗时秒，对应 $request_time")
    upstream_addr: Optional[str] = Field(default=None, description="上游地址，对应 $upstream_addr")
    upstream_status: Optional[int] = Field(default=None, ge=100, le=599, description="上游响应码，对应 $upstream_status")
    upstream_response_time: Optional[float] = Field(default=None, ge=0, description="上游响应耗时秒，对应 $upstream_response_time")
    upstream_connect_time: Optional[float] = Field(default=None, ge=0, description="连接上游耗时秒，对应 $upstream_connect_time")
    upstream_header_time: Optional[float] = Field(default=None, ge=0, description="接收上游响应头耗时秒，对应 $upstream_header_time")
    upstream_cache_status: Optional[NginxUpstreamStatus] = Field(default=None, description="上游缓存状态，对应 $upstream_cache_status")
    connection: Optional[str] = Field(default=None, description="连接序号，对应 $connection")
    connection_requests: Optional[int] = Field(default=None, ge=0, description="同连接请求数，对应 $connection_requests")
    pipe: Optional[str] = Field(default=None, description="请求是否流水线，对应 $pipe")
    gzip_ratio: Optional[float] = Field(default=None, ge=0, description="gzip 压缩率，对应 $gzip_ratio")
    ssl_protocol: Optional[str] = Field(default=None, description="TLS 协议版本，对应 $ssl_protocol")
    ssl_cipher: Optional[str] = Field(default=None, description="TLS cipher，对应 $ssl_cipher")
    error_level: Optional[str] = Field(default=None, description="Nginx error log 级别，如 error、warn、crit")
    error_message: Optional[str] = Field(default=None, description="Nginx error log 原始错误信息")


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
    WebServerLog,
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
    template: Optional[AggregateTemplate] = Field(
        default=None,
        description="预置聚合模板；提供时走六类模板实现，group_by 可省略",
    )
    group_by: Optional[AggregateField] = None
    interval: Optional[TimeInterval] = None
    top_n: int = 10
    filters: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def _require_template_or_group_by(self) -> "LogAggregateRequest":
        if self.template is None and self.group_by is None:
            raise ValueError("template 与 group_by 至少提供一个")
        return self


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


# =========================
# 统一信封 data 负载模型（API 层使用，宽松对齐 service 真实输出）
# =========================

class LogSearchItem(BaseModel):
    """日志列表项；`payload` 为原始完整文档，`status` 兼容字符串/数值。"""

    model_config = ConfigDict(extra="allow")

    log_id: str = ""
    timestamp: Optional[datetime] = None
    log_level: Optional[str] = None
    log_type: Optional[str] = None
    event_type: Optional[str] = None
    service_name: Optional[str] = None
    message: Optional[str] = None
    trace_id: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    status: Optional[Any] = None
    summary: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class LogSearchData(BaseModel):
    items: List[LogSearchItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_more: bool = False
    took_ms: Optional[int] = None


class LogFieldsData(BaseModel):
    """`/logs/fields`：不带 log_type 返回已注册类型；带 log_type 返回字段目录。"""

    model_config = ConfigDict(extra="allow")

    log_type: Optional[str] = None
    catalog: Optional[Dict[str, Any]] = None
    registered_log_types: Optional[List[str]] = None


class LogAggregateData(BaseModel):
    group_by: str
    interval: Optional[str] = None
    buckets: List[Dict[str, Any]] = Field(default_factory=list)
    took_ms: Optional[int] = None
    extra: Optional[Dict[str, Any]] = None
