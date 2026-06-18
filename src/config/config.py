from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    mongo_url: str = "mongodb://localhost:27017"
    # 🗄️ Registramos las dos bases de datos (Desarrollo y Pruebas)
    mongo_db_dev: str = "pdf_database_dev"
    mongo_db_test: str = "pdf_database_test"
    max_file_size_mb: int = 5

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8',
        extra='ignore' 
    )

settings = Settings()