from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# config/ 与 app/ 同级，位于 backend 根目录下：app/core/config.py -> parents[2] = backend
_LLM_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "LLM.yaml"

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


def _load_llm_yaml() -> dict[str, Any]:
    """读取 config/LLM.yaml 的 llm 段；文件缺失或解析失败时返回空字典（走默认/环境变量）。"""
    if not _LLM_CONFIG_PATH.exists():
        return {}
    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML 未安装，跳过 %s 加载", _LLM_CONFIG_PATH)
        return {}
    try:
        with _LLM_CONFIG_PATH.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except Exception:
        logger.exception("解析 LLM 配置文件失败：%s", _LLM_CONFIG_PATH)
        return {}
    section = data.get("llm", data)
    return section if isinstance(section, dict) else {}


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
    def _apply_llm_yaml(self) -> "Settings":
        """以 config/LLM.yaml 作为 LLM 配置的统一来源；非空环境变量优先于本文件。"""
        raw = _load_llm_yaml()
        if not raw:
            return self
        for field, (env_key, yaml_key) in _LLM_FIELD_MAP.items():
            env_val = os.getenv(env_key)
            if env_val is not None and env_val.strip() != "":
                continue  # 进程环境变量（非空）优先，保留当前值
            if yaml_key not in raw or raw[yaml_key] is None:
                continue
            value = raw[yaml_key]
            current = getattr(self, field)
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
                logger.warning("LLM 配置项 %s 取值非法：%r，已忽略", yaml_key, value)
                continue
            object.__setattr__(self, field, coerced)
        # analysis_model 为空时回退 default_model
        if not str(self.llm_analysis_model).strip():
            object.__setattr__(self, "llm_analysis_model", self.llm_default_model)
        return self


settings = Settings()
