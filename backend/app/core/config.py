from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # LangChain / LangGraph 分析编排（占位配置，待 M3+ 使用）
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


settings = Settings()
