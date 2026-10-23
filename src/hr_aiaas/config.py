from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


EnvironmentName = Literal[
    "development",
    "test",
    "production",
]

LogLevel = Literal[
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
]


class Settings(BaseSettings):
    """Validated backend configuration."""

    app_name: str = "HR-AIAAS API"
    app_description: str = (
        "Local-first AI-assisted HR recruitment platform"
    )
    app_version: str = "0.1.0"
    app_env: EnvironmentName = "development"
    app_debug: bool = False

    app_host: str = "127.0.0.1"
    app_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
    )

    database_url: str = (
        "sqlite+aiosqlite:///./storage/hr_aiaas.db"
    )

    document_storage_path: Path = Path(
        "./storage/documents"
    )
    export_storage_path: Path = Path(
        "./storage/exports"
    )
    backup_storage_path: Path = Path(
        "./storage/backups"
    )

    frontend_origin: str = "http://localhost:3000"

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_chat_model: str = "replace-with-approved-model"
    ollama_embedding_model: str = (
        "replace-with-approved-embedding-model"
    )

    session_secret: SecretStr = Field(
        min_length=32,
    )

    access_token_minutes: int = Field(
        default=15,
        ge=1,
        le=1440,
    )
    session_idle_minutes: int = Field(
        default=30,
        ge=1,
        le=1440,
    )

    max_upload_mb: int = Field(
        default=15,
        ge=1,
        le=100,
    )

    log_level: LogLevel = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator(
        "frontend_origin",
        "ollama_base_url",
    )
    @classmethod
    def remove_trailing_slash(
        cls,
        value: str,
    ) -> str:
        return value.rstrip("/")

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    def create_storage_directories(self) -> None:
        directories = (
            self.document_storage_path,
            self.export_storage_path,
            self.backup_storage_path,
        )

        for directory in directories:
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
