from contextlib import asynccontextmanager

from src.config.config import settings
from src.core.logging_config import configure_logging

# Configurar logging centralizado ANTES de importar FastAPI y routers.
# Se usa el nivel desde la configuración de la aplicación (LOG_LEVEL por defecto INFO).
configure_logging(
    "ms2-extraction",
    level=settings.logging_level,
)

# 1) Dependencias de la aplicación (importadas con el logging ya configurado).
from fastapi import FastAPI  # noqa: E402

from src.api.extract_api import router as extract_router  # noqa: E402
from src.core.exceptions import register_exception_handlers  # noqa: E402

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title="PDF Extract Text API",
    description="API para procesar PDFs y extraer texto de forma síncrona",
    version="0.1.0",
    lifespan=lifespan,
)

# Manejo centralizado de excepciones de dominio (AppError -> JSON HTTP)
register_exception_handlers(app)

app.include_router(extract_router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Servidor funcionando sin base de datos (stateless)"
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}