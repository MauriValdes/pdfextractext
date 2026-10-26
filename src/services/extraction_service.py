"""Servicio de extracción síncrona de texto con PyMuPDF.

A diferencia de DocumentService (flujo asíncrono: encola y el worker
procesa), este servicio extrae el texto en memoria y responde de
inmediato. Es el núcleo del Microservicio de Extracción y Benchmark.

OJO: la extracción es CPU-bound (no hay I/O). La capa de API debe
ejecutarla en un threadpool para no bloquear el event loop bajo carga.
"""
import io
import logging

import fitz  # PyMuPDF

from src.core.exceptions import ExtractionError
from src.schemas.extraction import ExtractionResponse

logger = logging.getLogger(__name__)

# Firma mágica de los archivos PDF (validación barata antes de parsear)
PDF_MAGIC_HEADER = b"%PDF-"


class ExtractionService:
    """Extrae texto y metadatos de un PDF de forma síncrona (SRP)."""

    def extract(self, file_bytes: bytes, filename: str = "") -> ExtractionResponse:
        """Procesa el PDF en memoria y devuelve texto + cantidad de páginas.

        Raises:
            ExtractionError: si el archivo no es un PDF válido o está corrupto.
        """
        # 1. Validación de firma: evitamos invocar al parser con basura obvia
        if not file_bytes.startswith(PDF_MAGIC_HEADER):
            raise ExtractionError(
                "El archivo no tiene la firma de un PDF válido"
            )

        # 2. Extracción eficiente: un solo recorrido del documento, en memoria
        try:
            with fitz.open(stream=io.BytesIO(file_bytes), filetype="pdf") as doc:
                content = "".join(page.get_text() for page in doc)
                page_count = doc.page_count
        except Exception as e:
            logger.error("Error al parsear el PDF '%s': %s", filename, e)
            raise ExtractionError(
                f"No se pudo extraer el texto de '{filename or 'archivo'}'"
            ) from e

        logger.info(
            "Extracción síncrona OK: '%s' -> %d página(s), %d caracteres",
            filename,
            page_count,
            len(content),
        )
        return ExtractionResponse(content=content, page_count=page_count)
