from fastapi import APIRouter
from app.schemas.diagnosis import DiagnosisRequest
from app.services.diagnosis.analyzer import analyze_logs

router = APIRouter()


@router.post("")
def diagnosis(payload: DiagnosisRequest) -> dict:
    return analyze_logs(payload)
