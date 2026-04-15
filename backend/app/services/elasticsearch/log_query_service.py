from app.schemas.log import LogSearchRequest


def search_logs(payload: LogSearchRequest) -> dict:
    filters = {k: v for k, v in payload.model_dump().items() if v not in (None, "")}
    return {
        "message": "这是日志查询服务占位实现，后续接 Elasticsearch 检索",
        "filters": filters,
        "items": [],
    }
