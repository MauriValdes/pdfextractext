from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.extract_api import router as extract_router
from src.core.exceptions import register_exception_handlers

@asynccontextmanager
async def lifespan(app: FastAPI):

    yield

app = FastAPI(
    title="PDF Extract Text API",
    description="API para procesar PDFs y extraer texto de forma síncrona",
    version="0.1.0",
    lifespan=lifespan
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