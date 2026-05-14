import os

from elasticsearch import Elasticsearch

from app.core.config import settings


def get_es_client() -> Elasticsearch:
    hosts = [h.strip() for h in settings.elasticsearch_hosts.split(",") if h.strip()]
    # 进程环境优先：兼容 task 在 import 之后才 load_dotenv 注入 ELASTIC_PASSWORD 等变量
    user = (
        (os.environ.get("ELASTICSEARCH_USERNAME") or "").strip()
        or (settings.elasticsearch_username or "elastic").strip()
    )
    password = (
        (os.environ.get("ELASTICSEARCH_PASSWORD") or os.environ.get("ELASTIC_PASSWORD") or "").strip()
        or (settings.elasticsearch_password or "").strip()
    )
    kw: dict[str, object] = {}
    if password:
        kw["basic_auth"] = (user, password)
    return Elasticsearch(hosts, **kw)
