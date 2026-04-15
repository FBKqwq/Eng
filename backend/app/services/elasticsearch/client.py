from elasticsearch import Elasticsearch
from app.core.config import settings


def get_es_client() -> Elasticsearch:
    hosts = [h.strip() for h in settings.elasticsearch_hosts.split(",") if h.strip()]
    return Elasticsearch(hosts)
