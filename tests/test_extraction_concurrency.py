"""Pruebas de serialización de extracción dentro de un proceso MS2."""

import asyncio
import threading
from contextlib import asynccontextmanager

import anyio
import httpx
import pytest

from src.main import app
from src.schemas.extraction import ExtractionResponse
from src.services.extraction_service import ExtractionService


@asynccontextmanager
async def running_app_client():
    """Abre el lifespan antes de enviar solicitudes a la aplicación ASGI."""
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


@pytest.mark.asyncio
async def test_two_extractions_never_overlap(monkeypatch):
    first_started = asyncio.Event()
    release_first = threading.Event()
    state_lock = threading.Lock()
    active = 0
    maximum_active = 0
    calls = 0
    loop = asyncio.get_running_loop()

    def controlled_extract(self, file_bytes, filename=""):
        nonlocal active, maximum_active, calls
        with state_lock:
            calls += 1
            call_number = calls
            active += 1
            maximum_active = max(maximum_active, active)

        if call_number == 1:
            loop.call_soon_threadsafe(first_started.set)
            release_first.wait()

        with state_lock:
            active -= 1
        return ExtractionResponse(content="ok", page_count=1)

    monkeypatch.setattr(ExtractionService, "extract", controlled_extract)

    async with running_app_client() as client:
        first_task = asyncio.create_task(raw_pdf_request(client))
        await first_started.wait()

        lock = app.state.extraction_lock
        observed_lock = ObservedLock(lock)
        app.state.extraction_lock = observed_lock

        second_task = asyncio.create_task(raw_pdf_request(client))
        await observed_lock.waiting.wait()

        with state_lock:
            assert active == 1
            assert maximum_active == 1
            assert calls == 1

        release_first.set()
        first_response, second_response = await asyncio.gather(first_task, second_task)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert maximum_active == 1
    assert calls == 2


@pytest.mark.asyncio
async def test_extraction_exception_releases_lock(monkeypatch):
    calls = 0

    def fail_once(self, file_bytes, filename=""):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("fallo de extracción")
        return ExtractionResponse(content="ok", page_count=1)

    monkeypatch.setattr(ExtractionService, "extract", fail_once)

    async with running_app_client() as client:
        failed_response = await raw_pdf_request(client)
        assert failed_response.status_code == 500
        assert not app.state.extraction_lock.locked()

        successful_response = await raw_pdf_request(client)

    assert successful_response.status_code == 200
    assert calls == 2


@pytest.mark.asyncio
async def test_cancelled_request_waiting_for_lock_does_not_keep_lock(monkeypatch):
    first_started = asyncio.Event()
    release_first = threading.Event()
    loop = asyncio.get_running_loop()
    calls = 0

    def controlled_extract(self, file_bytes, filename=""):
        nonlocal calls
        calls += 1
        if calls == 1:
            loop.call_soon_threadsafe(first_started.set)
            release_first.wait()
        return ExtractionResponse(content="ok", page_count=1)

    monkeypatch.setattr(ExtractionService, "extract", controlled_extract)

    async with running_app_client() as client:
        first_task = asyncio.create_task(raw_pdf_request(client))
        await first_started.wait()

        observed_lock = ObservedLock(app.state.extraction_lock)
        app.state.extraction_lock = observed_lock
        waiting_task = asyncio.create_task(raw_pdf_request(client))
        await observed_lock.waiting.wait()

        waiting_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await waiting_task

        assert observed_lock._lock.locked()
        assert calls == 1

        release_first.set()
        first_response = await first_task
        assert not observed_lock._lock.locked()

    assert first_response.status_code == 200
    assert calls == 1


@pytest.mark.asyncio
async def test_cancellation_during_thread_does_not_release_lock_early(monkeypatch):
    first_started = asyncio.Event()
    second_started = asyncio.Event()
    release_workers = threading.Event()
    loop = asyncio.get_running_loop()
    state_lock = threading.Lock()
    calls = 0
    active = 0
    maximum_active = 0
    cancel_scope_ready = asyncio.Event()
    cancel_scope_holder = []

    def controlled_extract(self, file_bytes, filename=""):
        nonlocal calls, active, maximum_active
        with state_lock:
            calls += 1
            call_number = calls
            active += 1
            maximum_active = max(maximum_active, active)

        if call_number == 1:
            loop.call_soon_threadsafe(first_started.set)
        elif call_number == 2:
            loop.call_soon_threadsafe(second_started.set)

        release_workers.wait()

        with state_lock:
            active -= 1
        return ExtractionResponse(content="ok", page_count=1)

    monkeypatch.setattr(ExtractionService, "extract", controlled_extract)

    async with running_app_client() as client:
        async def cancellable_request():
            with anyio.CancelScope() as cancel_scope:
                cancel_scope_holder.append(cancel_scope)
                cancel_scope_ready.set()
                return await raw_pdf_request(client)

        first_task = asyncio.create_task(cancellable_request())
        await first_started.wait()
        await cancel_scope_ready.wait()

        observed_lock = ObservedLock(app.state.extraction_lock)
        app.state.extraction_lock = observed_lock
        cancel_scope_holder[0].cancel()
        await asyncio.sleep(0)  # Yield to deliver cancellation; no time-based delay.

        second_task = asyncio.create_task(raw_pdf_request(client))
        await observed_lock.waiting.wait()

        with state_lock:
            assert calls == 1
            assert active == 1
            assert maximum_active == 1
        assert not first_task.done()

        release_workers.set()
        await asyncio.gather(first_task, second_task, return_exceptions=True)

    assert maximum_active == 1
    assert second_started.is_set()


@pytest.mark.asyncio
async def test_health_endpoint_responds_while_extraction_thread_is_blocked(monkeypatch):
    extraction_started = asyncio.Event()
    release_extraction = threading.Event()
    loop = asyncio.get_running_loop()

    def controlled_extract(self, file_bytes, filename=""):
        loop.call_soon_threadsafe(extraction_started.set)
        release_extraction.wait()
        return ExtractionResponse(content="ok", page_count=1)

    monkeypatch.setattr(ExtractionService, "extract", controlled_extract)

    async with running_app_client() as client:
        extraction_task = asyncio.create_task(raw_pdf_request(client))
        await extraction_started.wait()

        health_response = await client.get("/health")

        release_extraction.set()
        extraction_response = await extraction_task

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert extraction_response.status_code == 200
