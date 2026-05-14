import os

from elasticsearch import Elasticsearch

from app.core.config import settings


def _strip_credential_quotes(value: str) -> str:
    """去掉 .env 中误写的成对引号，例如 ELASTICSEARCH_PASSWORD='changeme'。"""
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
        return v[1:-1].strip()
    return v


def get_es_client() -> Elasticsearch:
    hosts = [h.strip() for h in settings.elasticsearch_hosts.split(",") if h.strip()]
    # 进程环境优先：兼容 task 在 import 之后才 load_dotenv 注入 ELASTIC_PASSWORD 等变量
    user = _strip_credential_quotes(
        (os.environ.get("ELASTICSEARCH_USERNAME") or "").strip()
        or (settings.elasticsearch_username or "elastic").strip()
    )
    raw_pw = (os.environ.get("ELASTICSEARCH_PASSWORD") or os.environ.get("ELASTIC_PASSWORD") or "").strip()
    if not raw_pw:
        raw_pw = (settings.elasticsearch_password or "").strip()
    password = _strip_credential_quotes(raw_pw)
    kw: dict[str, object] = {}
    if password:
        kw["basic_auth"] = (user, password)
    return Elasticsearch(hosts, **kw)