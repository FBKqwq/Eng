from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# config/ 与 app/ 同级，位于 backend 根目录下：app/core/config.py -> parents[2] = backend
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_LLM_CONFIG_PATH = _BACKEND_ROOT / "config" / "LLM.yaml"
_GATEWAY_CONFIG_PATH = _BACKEND_ROOT / "config" / "gateway.yaml"

# Settings.llm_* 字段 -> (环境变量名, config/LLM.yaml 内键名)
_LLM_FIELD_MAP: dict[str, tuple[str, str]] = {
    "llm_provider": ("LLM_PROVIDER", "provider"),
    "llm_api_key": ("LLM_API_KEY", "api_key"),
    "llm_base_url": ("LLM_BASE_URL", "api_base"),
    "llm_default_model": ("LLM_DEFAULT_MODEL", "model_name"),
    "llm_analysis_model": ("LLM_ANALYSIS_MODEL", "analysis_model"),
    "llm_timeout_seconds": ("LLM_TIMEOUT_SECONDS", "timeout_seconds"),
    "llm_temperature": ("LLM_TEMPERATURE", "temperature"),
}

# Settings 基础设施字段 -> (环境变量名, _load_gateway_yaml 扁平化后的键名)
_GATEWAY_FIELD_MAP: dict[str, tuple[str, str]] = {
    "kafka_bootstrap_servers": ("KAFKA_BOOTSTRAP_SERVERS", "kafka_bootstrap_servers"),
    "kafka_topic": ("KAFKA_TOPIC", "kafka_topic"),
    "elasticsearch_hosts": ("ELASTICSEARCH_HOSTS", "elasticsearch_hosts"),
    "elasticsearch_index_pattern": ("ELASTICSEARCH_INDEX_PATTERN", "elasticsearch_index_pattern"),
    "elasticsearch_username": ("ELASTICSEARCH_USERNAME", "elasticsearch_username"),
    "elasticsearch_password": ("ELASTICSEARCH_PASSWORD", "elasticsearch_password"),
    "kibana_base_url": ("KIBANA_BASE_URL", "kibana_base_url"),
    "logstash_hosts": ("LOGSTASH_HOSTS", "logstash_hosts"),
}


def _load_yaml_section(path: Path, section_key: str) -> dict[str, Any]:
    """读取 YAML 指定段；文件缺失或解析失败时返回空字典。"""
    if not path.exists():
        return {}
    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML 未安装，跳过 %s 加载", path)
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except Exception:
        logger.exception("解析配置文件失败：%s", path)
        return {}
    section = data.get(section_key, data)
    return section if isinstance(section, dict) else {}


def _normalize_gateway_host(raw_host: Any) -> str:
    host = str(raw_host or "localhost").strip()
    return host or "localhost"


def _first_non_empty(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _env_nonempty(*keys: str) -> bool:
    return any(os.getenv(key) is not None and str(os.getenv(key, "")).strip() != "" for key in keys)


def _load_gateway_yaml() -> dict[str, Any]:
    """读取 config/gateway.yaml 并扁平化为 Settings 可直接消费的键。"""
    raw = _load_yaml_section(_GATEWAY_CONFIG_PATH, "gateway")
    if not raw:
        return {}

    host = _normalize_gateway_host(raw.get("host"))
    kafka = raw.get("kafka", {})
    elasticsearch = raw.get("elasticsearch", {})
    kibana = raw.get("kibana", {})
    logstash = raw.get("logstash", {})

    kafka_section = kafka if isinstance(kafka, dict) else {}
    es_section = elasticsearch if isinstance(elasticsearch, dict) else {}
    kibana_section = kibana if isinstance(kibana, dict) else {}
    logstash_section = logstash if isinstance(logstash, dict) else {}

    kafka_port = kafka_section.get("port", 9092)
    es_scheme = _first_non_empty(es_section.get("scheme"), "http") or "http"
    es_port = es_section.get("port", 9200)

    kafka_bootstrap = _first_non_empty(kafka_section.get("bootstrap_servers"))
    if not kafka_bootstrap:
        kafka_bootstrap = f"{host}:{kafka_port}"

    es_hosts = _first_non_empty(es_section.get("hosts"))
    if not es_hosts:
        es_hosts = f"{es_scheme}://{host}:{es_port}"

    kibana_base = _first_non_empty(kibana_section.get("base_url"))
    if not kibana_base:
        kibana_base = f"http://{host}:5601"

    logstash_hosts = _first_non_empty(logstash_section.get("hosts"))
    if not logstash_hosts:
        logstash_hosts = f"http://{host}:9600"

    flat: dict[str, Any] = {
        "kafka_bootstrap_servers": kafka_bootstrap,
        "kafka_topic": kafka_section.get("topic", "app-logs"),
        "elasticsearch_hosts": es_hosts,
        "elasticsearch_index_pattern": es_section.get("index_pattern", "app-logs-*"),
        "elasticsearch_username": es_section.get("username", "elastic"),
        "kibana_base_url": kibana_base,
        "logstash_hosts": logstash_hosts,
    }
    es_password = _first_non_empty(es_section.get("password"))
    if es_password:
        flat["elasticsearch_password"] = es_password
    return flat


def _apply_yaml_overrides(
    instance: "Settings",
    raw: dict[str, Any],
    field_map: dict[str, tuple[str, str]],
    *,
    env_keys_by_field: dict[str, tuple[str, ...]] | None = None,
) -> None:
    """将 YAML 扁平字段写入 Settings；非空环境变量优先于 YAML。"""
    if not raw:
        return
    env_keys_by_field = env_keys_by_field or {}
    for field, (env_key, yaml_key) in field_map.items():
        extra_env_keys = env_keys_by_field.get(field, ())
        if _env_nonempty(env_key, *extra_env_keys):
            continue
        if yaml_key not in raw or raw[yaml_key] is None:
            continue
        value = raw[yaml_key]
        if isinstance(value, str) and value.strip() == "":
            continue
        current = getattr(instance, field)
        try:
            if isinstance(current, bool):
                coerced: Any = bool(value)
            elif isinstance(current, int):
                coerced = int(value)
            elif isinstance(current, float):
                coerced = float(value)
            else:
                coerced = str(value)
        except (TypeError, ValueError):
            logger.warning("YAML 配置项 %s 取值非法：%r，已忽略", yaml_key, value)
            continue
        object.__setattr__(instance, field, coerced)


def _load_llm_yaml() -> dict[str, Any]:
    """读取 config/LLM.yaml 的 llm 段；文件缺失或解析失败时返回空字典（走默认/环境变量）。"""
    return _load_yaml_section(_LLM_CONFIG_PATH, "llm")


class Settings(BaseSettings):
    app_name: str = "Smart Log Analysis Backend"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "app-logs"

    elasticsearch_hosts: str = "http://localhost:9200"
    elasticsearch_index_pattern: str = "app-logs-*"
    elasticsearch_username: str = "elastic"
    elasticsearch_password: str = Field(
        default="",
        validation_alias=AliasChoices(
            "ELASTICSEARCH_PASSWORD",
            "ELASTIC_PASSWORD",
        ),
    )
    kibana_base_url: str = "http://localhost:5601"

    logstash_hosts: str = "http://localhost:9600"

    docker_project_name: str = "location"
    docker_monitored_services: str = "kafka,elasticsearch,logstash,kibana,setup"

    log_producer_interval_seconds: int = 1

    # LangChain / LangGraph 大模型调用配置。
    # 统一来源为 config/LLM.yaml；非空的同名环境变量（LLM_*）优先级更高。
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_default_model: str = "gpt-4o-mini"
    llm_analysis_model: str = "gpt-4o"
    llm_timeout_seconds: int = 30
    llm_temperature: float = 0.2
    analysis_schedule_minutes: int = 15
    trigger_scan_seconds: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def _apply_yaml_configs(self) -> "Settings":
        """加载 config/gateway.yaml 与 config/LLM.yaml；非空环境变量优先于 YAML。"""
        _apply_yaml_overrides(
            self,
            _load_gateway_yaml(),
            _GATEWAY_FIELD_MAP,
            env_keys_by_field={"elasticsearch_password": ("ELASTIC_PASSWORD",)},
        )

        raw_llm = _load_llm_yaml()
        _apply_yaml_overrides(self, raw_llm, _LLM_FIELD_MAP)
        if raw_llm and not str(self.llm_analysis_model).strip():
            object.__setattr__(self, "llm_analysis_model", self.llm_default_model)
        return self


settings = Settings()
