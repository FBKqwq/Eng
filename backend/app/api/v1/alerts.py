"""预警 API。

接口：GET /api/v1/alerts/active、POST /api/v1/alerts/{id}/ack
统一信封：ApiResponse[AlertListData] / ApiResponse[AlertAckData]
"""

from fastapi import APIRouter, Query

from app.schemas.alert import AlertAckData, AlertAckRequest, AlertListData, AlertStatus
from app.schemas.response import ApiCode, ApiResponse, error_envelope, ok_envelope
from app.services.alert.alert_service import acknowledge_alert, list_active_alerts

router = APIRouter()


@router.get("/active", response_model=ApiResponse[AlertListData])
def active_alerts(limit: int = Query(default=50, ge=1, le=200)) -> ApiResponse[AlertListData]:
  result = list_active_alerts(limit=limit)
  if not result.get("ok"):
    return error_envelope(ApiCode.QUERY_FAILED, result.get("error") or result.get("message", ""))
  return ok_envelope(AlertListData(items=result.get("items", []), total=result.get("total", 0)))


@router.post("/{alert_id}/ack", response_model=ApiResponse[AlertAckData])
def ack_alert(alert_id: str, payload: AlertAckRequest) -> ApiResponse[AlertAckData]:
  result = acknowledge_alert(alert_id, operator=payload.operator)
  if not result.get("ok"):
    return error_envelope(
      ApiCode.QUERY_FAILED,
      result.get("error") or result.get("message", ""),
      data=AlertAckData(alert_id=alert_id),
    )
  return ok_envelope(
    AlertAckData(
      alert_id=result.get("alert_id", alert_id),
      status=result.get("status", AlertStatus.acknowledged),
    )
  )
