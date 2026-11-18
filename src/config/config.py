from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    max_file_size_mb: int = 5

    # Capacidad de admisión por proceso (Factor 8). Controla cuántas
    # solicitudes POST /extract pueden estar admitidas simultáneamente.
    # No confundir con la capacidad de extracción, serializada a 1 por
    # proceso mediante app.state.extraction_lock.
    max_admitted_extractions: int = 2

    # 📝 Nivel de logging
    log_level: str = "INFO"

    @field_validator("max_admitted_extractions")
    @classmethod
    def validate_max_admitted_extractions(cls, value: int) -> int:
        """La capacidad de admisión debe ser un entero positivo."""
        if value <= 0:
            raise ValueError("max_admitted_extractions debe ser un entero positivo")
        return value

    @property
    def logging_level(self) -> str:
        """Nivel de logging con valor por defecto INFO."""
        return self.log_level

settings = Settings()
