"""Tests del endpoint síncrono POST /extract (contrato del TP de estrés)."""
from unittest.mock import MagicMock

import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient

from src.api.extract_api import get_extraction_service
from src.config.config import settings
from src.core.exceptions import ExtractionError
from src.main import app
from src.schemas.extraction import ExtractionResponse

@pytest.fixture
def client():
    """Ejecuta cada prueba con el lifespan de la aplicación activo."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_service():
    """Sustituye el servicio real: este test valida la capa HTTP, no la lógica."""
    service = MagicMock()
    app.dependency_overrides[get_extraction_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_extraction_service, None)


def make_pdf_bytes(pages: int = 1, text: str = "Hola mundo") -> bytes:
    """Genera un PDF válido en memoria con N páginas de texto."""
    doc = fitz.open()
    for _ in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def test_extract_ok_exact_contract(mock_service, client):
    """El contrato exige 200 con exactamente {content, page_count}."""
    mock_service.extract.return_value = ExtractionResponse(
        content="texto extraido", page_count=3
    )

    files = {"file": ("doc.pdf", b"%PDF-1.4 dummy", "application/pdf")}
    response = client.post("/extract", files=files)

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"content", "page_count"}
    assert body["content"] == "texto extraido"
    assert body["page_count"] == 3
    mock_service.extract.assert_called_once()


def test_extract_rejects_non_pdf_mime(mock_service, client):
    files = {"file": ("doc.pdf", b"contenido", "text/plain")}
    response = client.post("/extract", files=files)

    assert response.status_code == 400
    mock_service.extract.assert_not_called()


def test_extract_rejects_non_pdf_extension(mock_service, client):
    files = {"file": ("notas.txt", b"contenido", "application/pdf")}
    response = client.post("/extract", files=files)

    assert response.status_code == 400
    mock_service.extract.assert_not_called()


def test_extract_rejects_empty_file(mock_service, client):
    files = {"file": ("vacio.pdf", b"", "application/pdf")}
    response = client.post("/extract", files=files)

    assert response.status_code == 400
    mock_service.extract.assert_not_called()


def test_extract_rejects_oversized_file(mock_service, client):
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    big_pdf = b"%PDF-1.4 " + b"a" * max_bytes  # supera el límite
    files = {"file": ("grande.pdf", big_pdf, "application/pdf")}
    response = client.post("/extract", files=files)

    assert response.status_code == 413
    mock_service.extract.assert_not_called()


def test_extract_corrupt_pdf_returns_422(mock_service, client):
    mock_service.extract.side_effect = ExtractionError()

    files = {"file": ("corrupto.pdf", b"%PDF-1.4 basura", "application/pdf")}
    response = client.post("/extract", files=files)

    assert response.status_code == 422
    assert "detail" in response.json()


def test_extract_end_to_end_with_real_pdf(client):
    """Integración: servicio real con un PDF generado en memoria."""
    pdf_bytes = make_pdf_bytes(pages=2, text="Contrato de benchmark")
    files = {"file": ("real.pdf", pdf_bytes, "application/pdf")}
    response = client.post("/extract", files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["page_count"] == 2
    assert "Contrato de benchmark" in body["content"]


def test_extract_raw_bytes_via_content_type(client):
    """Testear la vía de bytes directos con Content-Type: application/pdf
    (sin multipart/form-data). Esto cubre la rama 'else' en _extract_pdf_bytes_from_request."""
    mock_service = MagicMock()
    mock_service.extract.return_value = ExtractionResponse(
        content="texto extraido raw", page_count=1
    )
    app.dependency_overrides[get_extraction_service] = lambda: mock_service

    # Enviar bytes raw con Content-Type: application/pdf
    pdf_bytes = b"%PDF-1.4 texto raw de prueba"
    response = client.post(
        "/extract",
        content=pdf_bytes,
        headers={"Content-Type": "application/pdf"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["content"] == "texto extraido raw"
    assert body["page_count"] == 1

    app.dependency_overrides.pop(get_extraction_service, None)


def test_extract_raw_bytes_rejects_wrong_mime(client):
    """Testear que bytes raw con Content-Type incorrecto falla."""
    mock_service = MagicMock()
    app.dependency_overrides[get_extraction_service] = lambda: mock_service

    response = client.post(
        "/extract",
        content=b"%PDF-1.4 basura",
        headers={"Content-Type": "text/plain"},
    )

    assert response.status_code == 400
    mock_service.extract.assert_not_called()

    app.dependency_overrides.pop(get_extraction_service, None)
