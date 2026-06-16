"""预警 API（占位）。

规划：GET /api/v1/alerts/active、POST /api/v1/alerts/{id}/ack
"""

from fastapi import APIRouter, Query

from app.schemas.alert import AlertAckRequest, AlertAckResponse, AlertListResponse
from app.services.alert.alert_service import acknowledge_alert, list_active_alerts

router = APIRouter()


@router.get("/active", response_model=AlertListResponse)
def active_alerts(limit: int = Query(default=50, ge=1, le=200)) -> dict:
  result = list_active_alerts(limit=limit)
  return AlertListResponse(
    ok=result.get("ok", False),
    placeholder=result.get("placeholder", True),
    message=result.get("message", ""),
    items=[],
    total=result.get("total", 0),
  ).model_dump()


@router.post("/{alert_id}/ack", response_model=AlertAckResponse)
def ack_alert(alert_id: str, payload: AlertAckRequest) -> dict:
  result = acknowledge_alert(alert_id, operator=payload.operator)
  return AlertAckResponse(
    ok=result.get("ok", False),
    placeholder=result.get("placeholder", True),
    message=result.get("message", ""),
    alert_id=alert_id,
  ).model_dump()
