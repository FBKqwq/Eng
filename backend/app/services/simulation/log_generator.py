import random
import time
import uuid
from datetime import datetime, timezone
from typing import Any


def _now_ts() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _rand_ip() -> str:
    return f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


def _base_record(
    *,
    log_type: str,
    event_type: str,
    service_name: str,
    trace_id: str,
    status: int,
    response_time_ms: int,
    error_code: str,
    message: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    log_id = str(uuid.uuid4())
    request_id = f"req-{uuid.uuid4().hex[:16]}"
    session_id = f"sess-{random.randint(100000, 999999)}"
    tags = ["mock", "ecommerce", log_type]
    record: dict[str, Any] = {
        "timestamp": _now_ts(),
        "log_id": log_id,
        "log_level": "ERROR" if status >= 500 else ("WARN" if status >= 400 else "INFO"),
        "log_type": log_type,
        "event_type": event_type,
        "service_name": service_name,
        "trace_id": trace_id,
        "span_id": f"span-{uuid.uuid4().hex[:8]}",
        "request_id": request_id,
        "user_id": f"U{random.randint(1000, 9999)}",
        "session_id": session_id,
        "client_ip": _rand_ip(),
        "status": status,
        "status_code": status,
        "response_time_ms": response_time_ms,
        "error_code": error_code,
        "message": message,
        "tags": tags,
        "source_type": "backend_simulation",
        "env": "dev",
    }
    if extra:
        record["extra"] = extra
    return record


def _pick_http_status() -> tuple[int, str]:
    status = random.choices([200, 201, 400, 404, 429, 500, 503], weights=[55, 5, 8, 6, 4, 12, 5])[0]
    err = ""
    if status == 404:
        err = "NOT_FOUND"
    elif status == 429:
        err = "RATE_LIMITED"
    elif status == 400:
        err = "BAD_REQUEST"
    elif status >= 500:
        err = random.choice(["DB_TIMEOUT", "PAY_FAIL", "INTERNAL_ERROR", "CIRCUIT_OPEN"])
    return status, err


def _build_application(trace_id: str) -> dict[str, Any]:
    services = ["order-service", "user-service", "payment-service", "search-service", "inventory-service"]
    events = ["browse", "search", "submit_order", "pay", "stock_check", "refund_apply"]
    paths = {
        "browse": "/api/goods/list",
        "search": "/api/search",
        "submit_order": "/api/order/submit",
        "pay": "/api/pay",
        "stock_check": "/api/inventory/reserve",
        "refund_apply": "/api/order/refund",
    }
    event = random.choice(events)
    status, error_code = _pick_http_status()
    downstream = ""
    if status >= 500:
        downstream = random.choice(["mysql-primary", "redis-cluster", "payment-gateway"])
    retry_count = random.randint(0, 3) if status >= 500 else 0
    anomaly_signal = status >= 500 or random.random() < 0.08
    hints: list[str] = []
    if status >= 500:
        hints = ["检查下游超时与连接池", "核对支付渠道返回码", "查看同 trace 的库存服务日志"]
    elif status == 429:
        hints = ["检查网关限流策略与突发流量"]
    rec = _base_record(
        log_type="application",
        event_type=event,
        service_name=random.choice(services),
        trace_id=trace_id,
        status=status,
        response_time_ms=random.randint(20, 4800),
        error_code=error_code,
        message=f"应用请求完成: {event}",
    )
    rec["request_path"] = paths.get(event, "/api/unknown")
    rec["exception_type"] = "RuntimeError" if status >= 500 and random.random() < 0.4 else ""
    rec["downstream_service"] = downstream
    rec["retry_count"] = retry_count
    rec["anomaly_signal"] = anomaly_signal
    rec["diagnosis_hints"] = hints
    return rec


def _build_behavior(trace_id: str) -> dict[str, Any]:
    events = [
        "page_view",
        "product_click",
        "search_keyword",
        "add_to_cart",
        "checkout_click",
        "pay_button_click",
        "recommendation_click",
    ]
    event = random.choice(events)
    status, _ = _pick_http_status()
    if event in ("page_view", "product_click", "recommendation_click"):
        status = 200
    rec = _base_record(
        log_type="behavior",
        event_type=event,
        service_name="web-frontend-tracker",
        trace_id=trace_id,
        status=status,
        response_time_ms=random.randint(5, 800),
        error_code="",
        message=f"埋点事件: {event}",
    )
    rec["request_path"] = "/track/collect"
    rec["tracking"] = {
        "event_count": random.randint(1, 20),
        "click_count": random.randint(0, 15),
        "page_view_count": random.randint(1, 8),
        "unique_visitor_count": random.randint(1, 5),
        "dwell_time_ms": random.randint(200, 120000),
        "bounce": random.random() < 0.25,
        "conversion_step": random.choice(["awareness", "interest", "decision", "purchase", "loyalty"]),
    }
    rec["exception_type"] = ""
    rec["downstream_service"] = ""
    rec["retry_count"] = 0
    rec["anomaly_signal"] = rec["tracking"]["bounce"] and random.random() < 0.3
    rec["diagnosis_hints"] = [] if not rec["anomaly_signal"] else ["关注跳出率与落地页性能"]
    return rec


def _build_web_server(trace_id: str) -> dict[str, Any]:
    paths = [
        "/",
        "/goods/list",
        "/goods/detail/10086",
        "/api/goods/list",
        "/api/search",
        "/api/order/submit",
        "/api/pay",
        "/static/app.js",
        "/static/main.css",
    ]
    methods = ["GET", "GET", "GET", "POST", "POST"]
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 Safari/605.1.15",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
        "curl/8.4.0",
        "Googlebot/2.1 (+http://www.google.com/bot.html)",
    ]
    upstreams = ["order-service:8000", "search-service:8000", "payment-service:8000", "frontend-static:80"]
    path = random.choice(paths)
    method = random.choice(methods)
    status, error_code = _pick_http_status()
    if path.startswith("/static/") and status >= 500:
        status = random.choice([200, 304, 404])
        error_code = "NOT_FOUND" if status == 404 else ""

    request_time = round(random.uniform(0.003, 2.8 if status < 500 else 6.5), 3)
    upstream_response_time = None if path.startswith("/static/") else round(max(0.001, request_time - random.uniform(0.001, 0.08)), 3)
    query = ""
    if path == "/api/search":
        query = f"keyword={random.choice(['phone', 'laptop', 'shoes', 'coffee'])}&page={random.randint(1, 5)}"
    request_uri = f"{path}?{query}" if query else path
    protocol = random.choice(["HTTP/1.1", "HTTP/2.0"])
    request_line = f"{method} {request_uri} {protocol}"
    nginx_log_kind = "error" if status >= 500 and random.random() < 0.35 else "access"
    message = (
        f'nginx {nginx_log_kind}: "{request_line}" {status} '
        f'{int(request_time * 1000)}ms'
    )

    rec = _base_record(
        log_type="web_server",
        event_type=f"nginx_{nginx_log_kind}",
        service_name=random.choice(["nginx-gateway", "nginx-edge", "openresty-gateway"]),
        trace_id=trace_id,
        status=status,
        response_time_ms=int(request_time * 1000),
        error_code=error_code,
        message=message,
    )
    rec["nginx_log_kind"] = nginx_log_kind
    rec["remote_addr"] = rec["client_ip"]
    rec["remote_user"] = "-" if random.random() < 0.88 else f"user{random.randint(1000, 9999)}"
    rec["time_local"] = datetime.now().astimezone().strftime("%d/%b/%Y:%H:%M:%S %z")
    rec["request"] = request_line
    rec["request_method"] = method
    rec["request_uri"] = request_uri
    rec["uri"] = path
    rec["query_string"] = query or None
    rec["server_protocol"] = protocol
    rec["body_bytes_sent"] = random.randint(0, 280000 if path.startswith("/static/") else 48000)
    rec["bytes_sent"] = rec["body_bytes_sent"] + random.randint(200, 1600)
    rec["request_length"] = random.randint(120, 4096)
    rec["http_referer"] = random.choice(["-", "https://shop.example.com/", "https://shop.example.com/search"])
    rec["http_user_agent"] = random.choice(user_agents)
    rec["http_x_forwarded_for"] = f"{_rand_ip()}, 172.18.0.{random.randint(2, 254)}" if random.random() < 0.6 else None
    rec["host_header"] = random.choice(["shop.example.com", "api.shop.example.com", "localhost"])
    rec["server_name"] = random.choice(["shop.example.com", "api.shop.example.com"])
    rec["scheme"] = random.choice(["http", "https", "https"])
    rec["upstream_addr"] = None if path.startswith("/static/") else random.choice(upstreams)
    rec["upstream_status"] = None if path.startswith("/static/") else status
    rec["upstream_response_time"] = upstream_response_time
    rec["upstream_connect_time"] = None if upstream_response_time is None else round(random.uniform(0.001, 0.05), 3)
    rec["upstream_header_time"] = None if upstream_response_time is None else round(min(upstream_response_time, random.uniform(0.003, 0.2)), 3)
    rec["upstream_cache_status"] = random.choice(["HIT", "MISS", "BYPASS", "-"]) if method == "GET" else None
    rec["connection"] = str(random.randint(10000, 99999))
    rec["connection_requests"] = random.randint(1, 120)
    rec["pipe"] = random.choice([".", "p"])
    rec["gzip_ratio"] = round(random.uniform(1.2, 5.0), 2) if path.endswith((".js", ".css")) else None
    rec["ssl_protocol"] = random.choice(["TLSv1.2", "TLSv1.3"]) if rec["scheme"] == "https" else None
    rec["ssl_cipher"] = random.choice(["TLS_AES_256_GCM_SHA384", "ECDHE-RSA-AES128-GCM-SHA256"]) if rec["scheme"] == "https" else None
    rec["error_level"] = "error" if nginx_log_kind == "error" else None
    rec["error_message"] = (
        f"upstream timed out while reading response header from upstream {rec['upstream_addr']}"
        if nginx_log_kind == "error"
        else None
    )
    rec["anomaly_signal"] = status >= 500 or request_time > 3
    rec["diagnosis_hints"] = (
        ["检查 Nginx upstream 超时、网关连接数与后端服务响应时间"]
        if rec["anomaly_signal"]
        else []
    )
    return rec


def _build_performance(trace_id: str) -> dict[str, Any]:
    rec = _base_record(
        log_type="performance",
        event_type="apm_metric",
        service_name=random.choice(["order-service", "payment-service", "gateway"]),
        trace_id=trace_id,
        status=200,
        response_time_ms=random.randint(10, 2000),
        error_code="",
        message="性能采样上报",
    )
    rec["request_path"] = "/internal/metrics"
    rec["metrics"] = {
        "cpu_percent": round(random.uniform(5, 95), 2),
        "heap_used_mb": round(random.uniform(128, 900), 2),
        "gc_pause_ms": round(random.uniform(0, 120), 2),
        "thread_pool_active": random.randint(1, 64),
        "queue_depth": random.randint(0, 500),
    }
    rec["exception_type"] = ""
    rec["downstream_service"] = ""
    rec["retry_count"] = 0
    rec["anomaly_signal"] = rec["metrics"]["cpu_percent"] > 85 or rec["metrics"]["queue_depth"] > 350
    rec["diagnosis_hints"] = (
        ["CPU 或队列积压偏高，建议扩容或限流"] if rec["anomaly_signal"] else []
    )
    return rec


def _build_security(trace_id: str) -> dict[str, Any]:
    blocked = random.random() < 0.35
    status = 403 if blocked else 200
    rec = _base_record(
        log_type="security",
        event_type=random.choice(["waf_block", "login_anomaly", "token_replay", "ip_blacklist"]),
        service_name="security-gateway",
        trace_id=trace_id,
        status=status,
        response_time_ms=random.randint(3, 120),
        error_code="FORBIDDEN" if blocked else "",
        message="安全策略命中" if blocked else "安全扫描通过",
    )
    rec["request_path"] = "/auth/verify"
    rec["security"] = {
        "rule_id": random.choice(["SEC-001", "SEC-014", "SEC-022"]),
        "action": "block" if blocked else "allow",
        "risk_score": round(random.uniform(0, 1), 3),
    }
    rec["exception_type"] = ""
    rec["downstream_service"] = ""
    rec["retry_count"] = 0
    rec["anomaly_signal"] = blocked
    rec["diagnosis_hints"] = ["复核客户端指纹与地理位置"] if blocked else []
    return rec


def _build_infrastructure(trace_id: str) -> dict[str, Any]:
    component = random.choice(["kafka", "elasticsearch", "logstash", "backend"])
    healthy = random.random() > 0.12
    status = 200 if healthy else 503
    rec = _base_record(
        log_type="infrastructure",
        event_type="health_check",
        service_name=f"{component}-probe",
        trace_id=trace_id,
        status=status,
        response_time_ms=random.randint(2, 400),
        error_code="" if healthy else "UNAVAILABLE",
        message=f"组件 {component} 健康检查",
    )
    rec["request_path"] = "/health"
    rec["infra"] = {"component": component, "healthy": healthy, "latency_ms": rec["response_time_ms"]}
    rec["exception_type"] = "" if healthy else "ServiceUnavailable"
    rec["downstream_service"] = component
    rec["retry_count"] = 0 if healthy else random.randint(1, 4)
    rec["anomaly_signal"] = not healthy
    rec["diagnosis_hints"] = (
        ["检查容器资源与依赖端口"] if not healthy else []
    )
    return rec


def build_mock_log() -> dict[str, Any]:
    """生成单条结构化模拟日志，字段与 simulation/DEV.md 对齐，供 Kafka 与下游消费。"""
    trace_id = f"T-{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}"
    builders = [
        (_build_application, 42),
        (_build_behavior, 20),
        (_build_web_server, 18),
        (_build_performance, 10),
        (_build_security, 8),
        (_build_infrastructure, 2),
    ]
    fn = random.choices([b[0] for b in builders], weights=[b[1] for b in builders])[0]
    return fn(trace_id)
