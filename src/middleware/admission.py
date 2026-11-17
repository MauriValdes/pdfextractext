"""Middleware ASGI para admisión acotada de solicitudes de extracción."""

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from src.core.admission import AdmissionController


class AdmissionMiddleware:
    """Admite ``POST /extract`` sin encolar solicitudes cuando no hay cupo.

    El middleware recibe explícitamente el controlador y no depende de claves
    añadidas al scope por FastAPI o Starlette. La liberación cubre todo el
    tiempo durante el cual la aplicación ASGI interna procesa la solicitud.
    """

    def __init__(self, app: ASGIApp, admission: AdmissionController) -> None:
        self.app = app
        self.admission = admission

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        is_extract_post = (
            scope["type"] == "http"
            and scope.get("method") == "POST"
            and scope.get("path") == "/extract"
        )
        if not is_extract_post:
            await self.app(scope, receive, send)
            return

        permit = self.admission.try_acquire()
        if permit is None:
            response = JSONResponse(
                status_code=503,
                content={
                    "detail": "Servicio temporalmente saturado. Intente nuevamente."
                },
            )
            await response(scope, receive, send)
            return

        try:
            await self.app(scope, receive, send)
        finally:
            permit.release()
