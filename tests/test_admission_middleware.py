"""Pruebas aisladas del middleware ASGI de admisión."""

import asyncio
import json

import pytest

from src.core.admission import AdmissionController
from src.middleware.admission import AdmissionMiddleware


def make_scope(method: str = "POST", path: str = "/extract") -> dict:
    """Construye un scope HTTP ASGI mínimo sin ``scope['app']``."""
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [],
        "server": ("testserver", 80),
        "client": ("testclient", 12345),
    }


async def invoke_middleware(middleware, scope, receive):
    sent = []

    async def send(message):
        sent.append(message)

    await middleware(scope, receive, send)
    return sent


@pytest.mark.asyncio
async def test_admitted_request_reaches_inner_application_and_releases_permit():
    admission = AdmissionController(capacity=1)
    calls = []

    async def inner_app(scope, receive, send):
        calls.append(scope)
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok", "more_body": False})

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    middleware = AdmissionMiddleware(inner_app, admission)
    sent = await invoke_middleware(middleware, make_scope(), receive)

    assert len(calls) == 1
    response_starts = [
        message["status"]
        for message in sent
        if message["type"] == "http.response.start"
    ]
    assert response_starts == [200]
    assert admission.in_use == 0


@pytest.mark.asyncio
async def test_saturation_returns_json_503_without_calling_inner_app_or_receive():
    admission = AdmissionController(capacity=1)
    held_permit = admission.try_acquire()
    assert held_permit is not None
    inner_calls = []
    receive_calls = []

    async def inner_app(scope, receive, send):
        inner_calls.append(scope)

    async def receive():
        receive_calls.append(True)
        return {"type": "http.request", "body": b"PDF body", "more_body": False}

    middleware = AdmissionMiddleware(inner_app, admission)
    sent = await invoke_middleware(middleware, make_scope(), receive)

    response_start = next(
        message for message in sent if message["type"] == "http.response.start"
    )
    response_body = next(
        message for message in sent if message["type"] == "http.response.body"
    )
    assert response_start["status"] == 503
    assert (b"content-type", b"application/json") in response_start["headers"]
    assert json.loads(response_body["body"]) == {
        "detail": "Servicio temporalmente saturado. Intente nuevamente."
    }
    assert inner_calls == []
    assert receive_calls == []
    assert admission.in_use == 1

    held_permit.release()
    assert admission.in_use == 0


@pytest.mark.asyncio
async def test_permit_is_released_when_inner_application_raises():
    admission = AdmissionController(capacity=1)

    async def inner_app(scope, receive, send):
        raise RuntimeError("fallo interno")

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    middleware = AdmissionMiddleware(inner_app, admission)

    with pytest.raises(RuntimeError, match="fallo interno"):
        await invoke_middleware(middleware, make_scope(), receive)

    assert admission.in_use == 0


@pytest.mark.asyncio
async def test_permit_is_released_when_send_raises():
    admission = AdmissionController(capacity=1)

    async def inner_app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def failing_send(message):
        raise RuntimeError("fallo al enviar respuesta")

    middleware = AdmissionMiddleware(inner_app, admission)

    with pytest.raises(RuntimeError, match="fallo al enviar respuesta"):
        await middleware(make_scope(), receive, failing_send)

    assert admission.in_use == 0


@pytest.mark.asyncio
async def test_permit_remains_held_until_inner_application_finishes():
    admission = AdmissionController(capacity=1)
    started = asyncio.Event()
    finish = asyncio.Event()

    async def inner_app(scope, receive, send):
        started.set()
        await finish.wait()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok", "more_body": False})

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    middleware = AdmissionMiddleware(inner_app, admission)
    task = asyncio.create_task(invoke_middleware(middleware, make_scope(), receive))
    await started.wait()

    assert admission.in_use == 1
    assert not task.done()

    finish.set()
    await task
    assert admission.in_use == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/extract"),
        ("PUT", "/extract"),
        ("POST", "/extract/"),
        ("POST", "/extract/other"),
        ("POST", "/health"),
    ],
)
async def test_non_matching_requests_pass_through_without_admission(
    method, path, monkeypatch
):
    admission = AdmissionController(capacity=1)
    acquire_attempts = 0
    original_try_acquire = admission.try_acquire

    def track_try_acquire():
        nonlocal acquire_attempts
        acquire_attempts += 1
        return original_try_acquire()

    monkeypatch.setattr(admission, "try_acquire", track_try_acquire)
    calls = []

    async def inner_app(scope, receive, send):
        calls.append(scope)
        request = await receive()
        assert request["type"] == "http.request"
        assert request["body"] == b"request body"
        assert admission.in_use == 0
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b"", "more_body": False})

    receive_calls = []

    async def receive():
        receive_calls.append(True)
        return {
            "type": "http.request",
            "body": b"request body",
            "more_body": False,
        }

    middleware = AdmissionMiddleware(inner_app, admission)
    sent = await invoke_middleware(middleware, make_scope(method, path), receive)

    assert len(calls) == 1
    response_start = next(
        message for message in sent if message["type"] == "http.response.start"
    )
    assert response_start["status"] == 204
    assert admission.in_use == 0
    assert acquire_attempts == 0
    assert receive_calls == [True]


@pytest.mark.asyncio
async def test_closed_controller_rejects_without_calling_inner_app_or_receive():
    admission = AdmissionController(capacity=1)
    admission.close()
    inner_calls = []
    receive_calls = []

    async def inner_app(scope, receive, send):
        inner_calls.append(scope)

    async def receive():
        receive_calls.append(True)
        return {"type": "http.request", "body": b"", "more_body": False}

    middleware = AdmissionMiddleware(inner_app, admission)
    sent = await invoke_middleware(middleware, make_scope(), receive)

    response_start = next(
        message for message in sent if message["type"] == "http.response.start"
    )
    assert response_start["status"] == 503
    assert inner_calls == []
    assert receive_calls == []
    assert admission.in_use == 0
