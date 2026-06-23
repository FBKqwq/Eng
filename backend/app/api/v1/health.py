from fastapi import APIRouter
from pydantic import BaseModel

from app.schemas.response import ApiResponse, ok_envelope

router = APIRouter()


class HealthData(BaseModel):
    status: str = "ok"


@router.get("", response_model=ApiResponse[HealthData])
def health() -> ApiResponse[HealthData]:
    return ok_envelope(HealthData(status="ok"))
