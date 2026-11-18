"""Pruebas de integración del control de admisión en la aplicación real.

Ejercitan el camino HTTP completo de MS2: AdmissionMiddleware registrado en
src.main, AdmissionController compartido por proceso, el lifespan real y la
convivencia con app.state.extraction_lock. No se simula el middleware ni se
reemplaza la aplicación; el único doble es ExtractionService.extract, para
controlar de forma determinista el trabajo del thread.
"""

import asyncio
import threading
from contextlib import asynccontextmanager
from types import SimpleNamespace

import httpx
import pytest

from src.main import admission_controller, app
from src.schemas.extraction import ExtractionResponse
from src.services.extraction_service import ExtractionService

SATURATION_BODY = {
    "detail": "Servicio temporalmente saturado. Intente nuevamente."
}


@asynccontextmanager
async def running_app_client():
    """Abre el lifespan real antes de enviar solicitudes a la aplicación."""
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            yield client


class ObservedLock:
    """Instrumenta el lock real para detectar una solicitud esperando."""

    def __init__(self, lock: asyncio.Lock) -> None:
        self._lock = lock
        self.waiting = asyncio.Event()

    async def __aenter__(self):
        if self._lock.locked():
            self.waiting.set()
        await self._lock.acquire()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self._lock.release()


def raw_pdf_request(client):
    return client.post(
        "/extract",
        content=b"%PDF-test",
        headers={"Content-Type": "application/pdf"},
    )


@pytest.fixture(autouse=True)
def isolated_admission_state():
    """Aísla el estado compartido del controlador entre pruebas.

    El arranque garantiza admisión habilitada aunque una prueba anterior haya
    cerrado el controlador al salir de su lifespan. El cierre verifica la
    limpieza: ninguna prueba puede terminar con permisos ocupados.
    """
    admission_controller.reopen()
    yield
    assert admission_controller.in_use == 0, (
        "la prueba dejó permisos de admisión sin liberar"
    )


@pytest.fixture
async def controlled_extract(monkeypatch):
    """Reemplaza ExtractionService.extract por una versión controlable.

    Con ``block_first`` activo, la primera llamada se bloquea en un thread
    hasta que la prueba lo libere; el resto de las llamadas responde al
    instante. Nunca se bloquea el event loop: el mock corre vía
    run_in_threadpool igual que la extracción real.
    """
    state = SimpleNamespace(calls=0, block_first=False)
    state_lock = threading.Lock()
    first_started = asyncio.Event()
    release_first = threading.Event()
    loop = asyncio.get_running_loop()

    def extract(self_service, file_bytes, filename=""):
        with state_lock:
            state.calls += 1
            call_number = state.calls
        if state.block_first and call_number == 1:
            loop.call_soon_threadsafe(first_started.set)
            release_first.wait()
        return ExtractionResponse(content="texto extraido", page_count=1)

    monkeypatch.setattr(ExtractionService, "extract", extract)
    state.first_started = first_started
    state.release_first = release_first
    yield state


async def fill_admission_slots(client, controlled_extract):
    """Ocupa los dos cupos de admisión de forma determinista.

    Devuelve (first_task, second_task, observed_lock). La primera solicitud
    queda extrayendo en un thread bloqueado; la segunda queda esperando el
    lock. Al retornar, ambos permisos están ocupados y la capacidad agotada.
    """
    assert admission_controller.capacity == 2
    controlled_extract.block_first = True

    first_task = asyncio.create_task(raw_pdf_request(client))
    await controlled_extract.first_started.wait()

    observed_lock = ObservedLock(app.state.extraction_lock)
    app.state.extraction_lock = observed_lock

    second_task = asyncio.create_task(raw_pdf_request(client))
    await observed_lock.waiting.wait()

    assert admission_controller.in_use == admission_controller.capacity
    return first_task, second_task, observed_lock


async def release_and_collect(controlled_extract, *tasks):
    """Libera el bloqueo y recoleciona las respuestas aunque fallen aserciones."""
    controlled_extract.release_first.set()
    return await asyncio.gather(*tasks, return_exceptions=True)


async def test_capacity_admits_two_and_rejects_third(
    controlled_extract,
):
    """Tres POST /extract concurrentes: dos admitidos (200) y uno rechazado."""
    async with running_app_client() as client:
        first_task, second_task, _ = await fill_admission_slots(client, controlled_extract)

        try:
            third_task = asyncio.create_task(raw_pdf_request(client))
            third_response = await third_task

            assert third_response.status_code == 503
            assert third_response.json() == SATURATION_BODY
            # El rechazo es inmediato y no altera la ocupación actual.
            assert admission_controller.in_use == admission_controller.capacity
        finally:
            first_response, second_response = await release_and_collect(
                controlled_extract, first_task, second_task
            )

        assert first_response.status_code == 200
        assert second_response.status_code == 200

    # La solicitud rechazada nunca llegó al servicio de extracción.
    assert controlled_extract.calls == 2
    assert admission_controller.in_use == 0


async def test_closed_controller_rejects_extract_but_health_works(
    controlled_extract,
):
    """Cerrado: /extract responde 503 y /health sigue funcionando."""
    async with running_app_client() as client:
        admission_controller.close()

        rejected = await raw_pdf_request(client)
        assert rejected.status_code == 503
        assert rejected.json() == SATURATION_BODY
        assert controlled_extract.calls == 0

        health = await client.get("/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}

        admission_controller.reopen()
        admitted = await raw_pdf_request(client)
        assert admitted.status_code == 200

    assert admission_controller.in_use == 0


async def test_non_admitted_routes_do_not_consume_capacity(
    controlled_extract,
):
    """GET /health y GET / funcionan con la capacidad de admisión agotada."""
    async with running_app_client() as client:
        first_task, second_task, _ = await fill_admission_slots(client, controlled_extract)

        try:
            health = await client.get("/health")
            root = await client.get("/")

            assert health.status_code == 200
            assert health.json() == {"status": "ok"}
            assert root.status_code == 200
            # Las rutas ajenas no consumen ni liberan permisos.
            assert admission_controller.in_use == admission_controller.capacity
        finally:
            await release_and_collect(controlled_extract, first_task, second_task)

    assert admission_controller.in_use == 0


async def test_lifespan_closes_and_reopens_controller(
    controlled_extract,
):
    """El lifespan real cierra el controlador y el siguiente ciclo lo reabre."""
    assert admission_controller.accepting

    async with app.router.lifespan_context(app):
        assert admission_controller.accepting
    assert not admission_controller.accepting

    async with app.router.lifespan_context(app):
        assert admission_controller.accepting
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            response = await raw_pdf_request(client)
        assert response.status_code == 200
    assert not admission_controller.accepting

    assert admission_controller.in_use == 0
