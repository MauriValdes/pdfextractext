"""Tests de la capa de servicio de extracción síncrona (sin HTTP)."""
import fitz  # PyMuPDF
import pytest

from src.core.exceptions import ExtractionError
from src.services.extraction_service import ExtractionService


def make_pdf_bytes(pages: int = 1, text: str = "Hola mundo") -> bytes:
    """Genera un PDF válido en memoria con N páginas de texto."""
    doc = fitz.open()
    for _ in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def test_extract_returns_content_and_page_count():
    service = ExtractionService()
    result = service.extract(make_pdf_bytes(pages=3), "triple.pdf")

    assert result.page_count == 3
    assert "Hola mundo" in result.content


def test_extract_rejects_non_pdf_bytes():
    service = ExtractionService()
    with pytest.raises(ExtractionError):
        service.extract(b"esto no es un pdf", "falso.pdf")


def test_extract_rejects_corrupt_pdf():
    service = ExtractionService()
    # Tiene la firma %PDF- pero el cuerpo está truncado/corrupto
    with pytest.raises(ExtractionError):
        service.extract(b"%PDF-1.4 basura truncada", "corrupto.pdf")
