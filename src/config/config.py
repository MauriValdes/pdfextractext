from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    mongo_url: str = "mongodb://localhost:27017"
    # Registramos las dos bases de datos (Desarrollo y Pruebas)
    mongo_db_dev: str = "pdf_database_dev"
    mongo_db_test: str = "pdf_database_test"
    max_file_size_mb: int = 5
    mongo_collection: str = "processed_pdfs"

    # 📝 Nivel de logging
    log_level: str = "INFO"

    # 🔴 Broker Redis (cola de tareas) - llega por variables de entorno (12-Factor)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_queue_key: str = "pdf:extract_text"
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8',
        extra='ignore' 
    )

    @property
    def logging_level(self) -> str:
        """Nivel de logging con valor por defecto INFO."""
        return self.log_level

    @property
    def redis_url(self) -> str:
        """URL de conexión al broker, derivada de host, puerto y base de datos."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

settings = Settings()