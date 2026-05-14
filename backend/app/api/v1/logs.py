from fastapi import APIRouter
from app.schemas.log import LogQueryRequest
from app.services.elasticsearch.log_query_service import search_logs

router = APIRouter()


@router.post("/search")
def log_search(payload: LogQueryRequest) -> dict:
    return search_logs(payload)
