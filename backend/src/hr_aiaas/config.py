from functools import lru_cache
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HR-AIAAS API"
    app_env: str = "development"
    app_debug: bool = False
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    database_url: str
    document_storage_path: str
    export_storage_path: str
    backup_storage_path: str

    frontend_origin: str = "http://localhost:3000"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_chat_model: str
    ollama_embedding_model: str

    session_secret: SecretStr
    access_token_minutes: int = 15
    session_idle_minutes: int = 30
    max_upload_mb: int = 15
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()