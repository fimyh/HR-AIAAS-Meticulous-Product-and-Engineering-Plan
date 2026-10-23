from pathlib import Path

from hr_aiaas.config import Settings


def test_settings_accept_valid_configuration() -> None:
    settings = Settings(
        session_secret="a" * 48,
    )

    assert settings.app_name == "HR-AIAAS API"
    assert settings.app_port == 8000
    assert settings.max_upload_mb == 15
    assert settings.max_upload_bytes == 15 * 1024 * 1024


def test_service_urls_remove_trailing_slashes() -> None:
    settings = Settings(
        session_secret="a" * 48,
        frontend_origin="http://localhost:3000/",
        ollama_base_url="http://127.0.0.1:11434/",
    )

    assert settings.frontend_origin == "http://localhost:3000"
    assert settings.ollama_base_url == "http://127.0.0.1:11434"


def test_environment_helpers() -> None:
    settings = Settings(
        session_secret="a" * 48,
        app_env="test",
    )

    assert settings.is_test is True
    assert settings.is_development is False
    assert settings.is_production is False


def test_create_storage_directories(
    tmp_path: Path,
) -> None:
    settings = Settings(
        session_secret="a" * 48,
        document_storage_path=tmp_path / "documents",
        export_storage_path=tmp_path / "exports",
        backup_storage_path=tmp_path / "backups",
    )

    settings.create_storage_directories()

    assert settings.document_storage_path.is_dir()
    assert settings.export_storage_path.is_dir()
    assert settings.backup_storage_path.is_dir()
