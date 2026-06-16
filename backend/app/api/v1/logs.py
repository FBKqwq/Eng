from fastapi import APIRouter, Query
from app.schemas.log import LogAggregateRequest, LogQueryRequest
from app.services.elasticsearch.aggregation_service import aggregate
from app.services.elasticsearch.log_query_service import search_logs
from app.services.elasticsearch.field_catalog import get_catalog_for_log_type, list_registered_log_types

router = APIRouter()


@router.post("/search")
def log_search(payload: LogQueryRequest) -> dict:
    return search_logs(payload)


@router.get("/fields")
def log_fields(log_type: str | None = Query(default=None, description="日志大类，如 application")) -> dict:
    """返回指定 log_type 的可筛选/聚合字段目录，或列出已注册类型。"""
    if log_type:
        catalog = get_catalog_for_log_type(log_type)
        if catalog.get("ok") is False:
            return {"ok": False, "message": catalog["message"]}
        return {"ok": True, "log_type": log_type, "catalog": catalog}
    return {"ok": True, "registered_log_types": list_registered_log_types()}


@router.post("/aggregate")
def log_aggregate(payload: LogAggregateRequest) -> dict:
    return aggregate(payload)
