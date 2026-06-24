from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.logs import router as logs_router
from app.api.v1.diagnosis import router as diagnosis_router
from app.api.v1.system import router as system_router
from app.api.v1.reports import router as reports_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.prediction import router as prediction_router
from app.api.v1.log_analysis import router as log_analysis_router
from app.api.v1.root_cause import router as root_cause_router
from app.api.v1.log_qa import router as log_qa_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/v1/health", tags=["health"])
api_router.include_router(logs_router, prefix="/v1/logs", tags=["logs"])
api_router.include_router(diagnosis_router, prefix="/v1/diagnosis", tags=["diagnosis"])
api_router.include_router(system_router, prefix="/v1/system", tags=["system"])
api_router.include_router(reports_router, prefix="/v1/reports", tags=["reports"])
api_router.include_router(alerts_router, prefix="/v1/alerts", tags=["alerts"])
api_router.include_router(analysis_router, prefix="/v1/analysis", tags=["analysis"])
api_router.include_router(prediction_router, prefix="/v1/prediction", tags=["prediction"])
api_router.include_router(log_analysis_router, prefix="/v1/log_analysis", tags=["log_analysis"])
api_router.include_router(root_cause_router, prefix="/v1/root_cause", tags=["root_cause"])
api_router.include_router(log_qa_router, prefix="/v1/log_qa", tags=["log_qa"])
