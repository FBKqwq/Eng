from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.logs import router as logs_router
from app.api.v1.diagnosis import router as diagnosis_router
from app.api.v1.system import router as system_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/v1/health", tags=["health"])
api_router.include_router(logs_router, prefix="/v1/logs", tags=["logs"])
api_router.include_router(diagnosis_router, prefix="/v1/diagnosis", tags=["diagnosis"])
api_router.include_router(system_router, prefix="/v1/system", tags=["system"])
