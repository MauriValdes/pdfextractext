"""Pruebas de las variables de entorno que utiliza MS2."""

from src.config.config import Settings


def test_settings_use_only_extraction_configuration(monkeypatch):
    monkeypatch.setenv("MAX_FILE_SIZE_MB", "12")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings()

    assert settings.max_file_size_mb == 12
    assert settings.log_level == "DEBUG"
    assert Settings.model_config.get("env_file") is None
