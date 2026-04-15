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

    log_producer_interval_seconds: int = 1

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
