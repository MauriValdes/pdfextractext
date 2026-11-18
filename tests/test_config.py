"""Pruebas de las variables de entorno que utiliza MS2."""

import pytest
from pydantic import ValidationError

from src.config.config import Settings


def test_settings_use_only_extraction_configuration(monkeypatch):
    monkeypatch.setenv("MAX_FILE_SIZE_MB", "12")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings()

    assert settings.max_file_size_mb == 12
    assert settings.log_level == "DEBUG"
    assert Settings.model_config.get("env_file") is None


def test_settings_default_max_admitted_extractions(monkeypatch):
    """Sin variable de entorno, la capacidad de admisión predeterminada es 2."""
    monkeypatch.delenv("MAX_ADMITTED_EXTRACTIONS", raising=False)

    settings = Settings()

    assert settings.max_admitted_extractions == 2


def test_settings_reads_max_admitted_extractions_from_env(monkeypatch):
    monkeypatch.setenv("MAX_ADMITTED_EXTRACTIONS", "7")

    settings = Settings()

    assert settings.max_admitted_extractions == 7


@pytest.mark.parametrize("value", ["0", "-1", "abc"])
def test_settings_rejects_invalid_max_admitted_extractions(monkeypatch, value):
    """La capacidad de admisión debe ser un entero positivo."""
    monkeypatch.setenv("MAX_ADMITTED_EXTRACTIONS", value)

    with pytest.raises(ValidationError):
        Settings()
