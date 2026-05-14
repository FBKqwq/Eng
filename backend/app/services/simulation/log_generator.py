import random
import time
from datetime import datetime


def build_mock_log() -> dict:
    services = ["order-service", "user-service", "payment-service", "search-service"]
    events = ["browse", "search", "submit_order", "pay"]
    status_code = random.choice([200, 200, 200, 500, 404])
    error_code = ""
    if status_code == 500:
        error_code = random.choice(["DB_TIMEOUT", "PAY_FAIL", "INTERNAL_ERROR"])
    elif status_code == 404:
        error_code = "NOT_FOUND"

    return {
        "timestamp": datetime.now().isoformat(),
        "log_level": random.choice(["INFO", "WARN", "ERROR"]),
        "service_name": random.choice(services),
        "event_type": random.choice(events),
        "user_id": f"U{random.randint(1000, 9999)}",
        "trace_id": f"T{int(time.time() * 1000)}",
        "request_path": random.choice(["/api/goods/list", "/api/search", "/api/order/submit", "/api/pay"]),
        "status_code": status_code,
        "response_time_ms": random.randint(50, 5000),
        "error_code": error_code,
        "message": "mock log from backend scaffold",
        "source_type": "backend",
        "env": "dev",
    }
