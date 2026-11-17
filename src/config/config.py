from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    max_file_size_mb: int = 5

    # 📝 Nivel de logging
    log_level: str = "INFO"

    @property
    def logging_level(self) -> str:
        """Nivel de logging con valor por defecto INFO."""
        return self.log_level

settings = Settings()
