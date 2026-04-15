from fastapi import FastAPI
from app.core.config import settings
from app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="模拟电商实时日志分析与智能诊断后端骨架",
    )
    app.include_router(api_router, prefix="/api")

    @app.get("/")
    def root() -> dict:
        return {
            "message": "backend scaffold is running",
            "app": settings.app_name,
            "env": settings.app_env,
        }

    return app


app = create_app()
