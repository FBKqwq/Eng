from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router
from app.api.v1.ws import (
    websocket_alerts,
    websocket_logs,
    websocket_system,
    send_alert_message,
    send_log_message,
    send_system_message,
)


LOCAL_DEV_ORIGIN_REGEX = (
    r"^https?://("
    r"localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|192\.168\.\d{1,3}\.\d{1,3}"
    r"):\d+$"
)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="模拟电商实时日志分析与智能诊断后端骨架",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=LOCAL_DEV_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api")

    # WebSocket endpoints
    app.add_api_websocket_route("/api/v1/ws/alerts", websocket_alerts)
    app.add_api_websocket_route("/api/v1/ws/logs", websocket_logs)
    app.add_api_websocket_route("/api/v1/ws/system", websocket_system)

    @app.get("/")
    def root() -> dict:
        return {
            "message": "backend scaffold is running",
            "app": settings.app_name,
            "env": settings.app_env,
        }

    return app


app = create_app()

# Export functions for sending messages
__all__ = ["send_alert_message", "send_log_message", "send_system_message"]
