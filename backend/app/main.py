from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router


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

    @app.get("/")
    def root() -> dict:
        return {
            "message": "backend scaffold is running",
            "app": settings.app_name,
            "env": settings.app_env,
        }

    @app.get("/health")
    def liveness() -> dict:
        """Liveness 探针：不依赖任何外部依赖，进程存活即返回 ok。"""
        return {"status": "ok"}

    return app


app = create_app()
