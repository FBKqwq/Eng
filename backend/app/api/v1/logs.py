from fastapi import APIRouter
from app.schemas.log import LogSearchRequest
from app.services.elasticsearch.log_query_service import search_logs

router = APIRouter()


@router.post("/search")
def log_search(payload: LogSearchRequest) -> dict:
    return search_logs(payload)
