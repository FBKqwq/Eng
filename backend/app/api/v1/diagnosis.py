from fastapi import APIRouter

from app.schemas.diagnosis import DiagnosisFacadeData, DiagnosisRequest
from app.schemas.response import ApiResponse, ok_envelope
from app.services.diagnosis.analyzer import analyze_logs

router = APIRouter()


@router.post("", response_model=ApiResponse[DiagnosisFacadeData])
def diagnosis(payload: DiagnosisRequest) -> ApiResponse[DiagnosisFacadeData]:
    return ok_envelope(DiagnosisFacadeData(**analyze_logs(payload)))
