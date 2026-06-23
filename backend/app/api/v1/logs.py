from fastapi import APIRouter, Query

from app.schemas.log import (
    LogAggregateData,
    LogAggregateRequest,
    LogFieldsData,
    LogQueryRequest,
    LogSearchData,
)
from app.schemas.response import ApiCode, ApiResponse, error_envelope, ok_envelope
from app.services.elasticsearch.aggregation_service import aggregate, aggregate_by_template
from app.services.elasticsearch.field_catalog import get_catalog_for_log_type, list_registered_log_types
from app.services.elasticsearch.log_query_service import search_logs

router = APIRouter()


@router.post("/search", response_model=ApiResponse[LogSearchData])
def log_search(payload: LogQueryRequest) -> ApiResponse[LogSearchData]:
    result = search_logs(payload)
    data = LogSearchData(**result)
    if not result.get("available", False):
        return error_envelope(
            ApiCode.ES_UNAVAILABLE,
            result.get("error") or "elasticsearch unavailable",
            data=data,
        )
    return ok_envelope(data)


@router.get("/fields", response_model=ApiResponse[LogFieldsData])
def log_fields(
    log_type: str | None = Query(default=None, description="日志大类，如 application")
) -> ApiResponse[LogFieldsData]:
    """返回指定 log_type 的可筛选/聚合字段目录，或列出已注册类型。"""
    if log_type:
        catalog = get_catalog_for_log_type(log_type)
        if catalog.get("ok") is False:
            return error_envelope(ApiCode.INVALID_PARAM, catalog.get("message", "invalid log_type"))
        return ok_envelope(LogFieldsData(log_type=log_type, catalog=catalog))
    return ok_envelope(LogFieldsData(registered_log_types=list_registered_log_types()))


@router.post("/aggregate", response_model=ApiResponse[LogAggregateData])
def log_aggregate(payload: LogAggregateRequest) -> ApiResponse[LogAggregateData]:
    result = aggregate_by_template(payload) if payload.template else aggregate(payload)
    data = LogAggregateData(**result)
    if not result.get("available", False):
        return error_envelope(
            ApiCode.ES_UNAVAILABLE,
            result.get("error") or "elasticsearch unavailable",
            data=data,
        )
    return ok_envelope(data)
