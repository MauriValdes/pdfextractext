from contextlib import asynccontextmanager
import asyncio

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
from src.core.admission import AdmissionController  # noqa: E402
from src.core.exceptions import register_exception_handlers  # noqa: E402
from src.middleware.admission import AdmissionMiddleware  # noqa: E402

# 2) Control de admisión acotada por proceso (Factor 8). Una única instancia
# por proceso/event loop; la capacidad se fija en el arranque desde la
# configuración (MAX_ADMITTED_EXTRACTIONS, valor predeterminado 2). No
# confundir con la capacidad de extracción, serializada a 1 por proceso
# mediante app.state.extraction_lock.
admission_controller = AdmissionController(
    capacity=settings.max_admitted_extractions,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # El arranque habilita nuevas admisiones; recupera el controlador de un
    # close() anterior (apagado previo o ciclo de pruebas).
    admission_controller.reopen()
    app.state.extraction_lock = asyncio.Lock()
    try:
        yield
    finally:
        # El apagado deja de admitir solicitudes nuevas (drain con 503); los
        # permisos ya concedidos siguen siendo válidos y se liberan con normalidad.
        admission_controller.close()
        app.state.extraction_lock = None

app = FastAPI(
    title="PDF Extract Text API",
    description="API para procesar PDFs y extraer texto de forma síncrona",
    version="0.1.0",
    lifespan=lifespan,
)

# 3) Middleware de admisión: aplica el control solo a POST /extract y responde
# 503 cuando no hay capacidad. Debe registrarse aquí, antes de que la
# aplicación reciba su primer scope: el stack ASGI se construye en ese primer
# uso (antes incluso del lifespan) y add_middleware falla después.
app.add_middleware(AdmissionMiddleware, admission=admission_controller)

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
