"""Application configuration via Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central application configuration.

    All values can be overridden via environment variables or .env file.
    """

    # --- App ---
    app_name: str = "content-factory"
    debug: bool = False
    log_level: str = "INFO"

    # --- Database ---
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/content_factory"

    # --- S3 / MinIO ---
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "content-factory"

    # --- Temporal ---
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"

    # --- LLM ---
    llm_provider: str = "openai"
    llm_model: str = ""  # optional override (e.g. "gpt-4o-mini", "claude-sonnet-4-5-20250929")
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # --- Observability ---
    sentry_dsn: str = ""
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
