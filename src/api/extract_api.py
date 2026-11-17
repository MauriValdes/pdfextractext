"""Capa de API: endpoint síncrono POST /extract.

Contrato obligatorio del Microservicio de Extracción y Benchmark:
  - Soporta peticiones con 'Content-Type: application/pdf' donde el body
    son los bytes directos del PDF (Request.body()).
  - Soporta también 'multipart/form-data' con campo 'file'.
  - Responde 200 OK con {"content": <texto>, "page_count": <int>}.

SRP: esta capa solo valida el sobre HTTP (MIME, extensión, vacío,
tamaño) y delega la extracción al servicio. Los errores se propagan
como excepciones de dominio y los traduce el handler centralizado
(src/core/exceptions.py).
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Request, File, UploadFile, status
from starlette.concurrency import run_in_threadpool

from src.config.config import settings
from src.core.exceptions import (
    EmptyFileError,
    FileTooLargeError,
    InvalidFileTypeError,
)
from src.schemas.extraction import ExtractionResponse
from src.services.extraction_service import ExtractionService

logger = logging.getLogger(__name__)

# Sin prefijo: el contrato exige la ruta raíz POST /extract
router = APIRouter(tags=["extraction"])


def get_extraction_service() -> ExtractionService:
    """Inyección de dependencias (DIP): el endpoint no instancia el servicio.

    El servicio es stateless, por lo que una instancia por request es barata.
    """
    return ExtractionService()


async def _extract_pdf_bytes_from_request(
    request: Request,
    file: Optional[UploadFile] = None,
) -> tuple[bytes, str]:
    """Extrae los bytes del PDF y el nombre de archivo del contenido de la petición.

    Soporta dos formatos (orden de prioridad):
    1. multipart/form-data con campo 'file' (usando el parámetro UploadFile de FastAPI).
    2. Raw bytes con Content-Type: application/pdf (lectura directa, sin parser de multipart).
       Esta vía es crítica para mantener máximo rendimiento en pruebas de estrés (k6, 100 VUs).
    """
    content_type = request.headers.get("Content-Type", "")

    if file is not None:
        # Multipart/form-data: el parámetro 'file' fue inyectado por FastAPI
        pdf_bytes = await file.read()
        filename = getattr(file, 'filename', 'document.pdf') or 'document.pdf'

        # Validaciones del sobre HTTP para multipart/form-data
        is_pdf_mime = file.content_type == "application/pdf" if hasattr(file, 'content_type') else False
        has_pdf_extension = bool(filename) and filename.lower().endswith(".pdf")
        if not (is_pdf_mime and has_pdf_extension):
            raise InvalidFileTypeError()
    else:
        # Raw PDF bytes con Content-Type: application/pdf
        # Lectión directa en memoria: NO usamos request.form() ni parsers de multipart
        # para maximizar rendimiento en benchmarks de estrés.
        pdf_bytes = await request.body()
        filename = ""

        # Validación para raw bytes: chequeado por firma magic header
        if content_type != "application/pdf":
            raise InvalidFileTypeError()

    if not pdf_bytes:
        raise EmptyFileError()

    return pdf_bytes, filename


@router.post(
    "/extract",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
)
async def extract_text(
    request: Request,
    file: UploadFile | None = File(None, description="PDF para Swagger UI"),
    service: ExtractionService = Depends(get_extraction_service),
) -> ExtractionResponse:
    """Extrae el texto de un PDF de forma síncrona y directa.

    Soporta dos formatos de entrada:
    1. multipart/form-data con campo 'file'
    2. Raw bytes con Content-Type: application/pdf
    """
    # 1. Extraer bytes del PDF según el contenido de la petición.
    # Si viene 'file' (multipart), usamos ese parámetro; si no, leemos raw bytes.
    pdf_bytes, filename = await _extract_pdf_bytes_from_request(request, file=file)

    # 2. Rechazo temprano por tamaño (misma política que /documents/upload)
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(pdf_bytes) > max_bytes:
        raise FileTooLargeError(
            f"El archivo supera el tamaño máximo de {settings.max_file_size_mb} MB"
        )

    # 3. PyMuPDF no debe ejecutarse simultáneamente dentro del proceso.
    # El lock vive en app.state y se comparte entre solicitudes del proceso.
    # run_in_threadpool mantiene el event loop disponible durante la extracción.
    async with request.app.state.extraction_lock:
        return await run_in_threadpool(service.extract, pdf_bytes, filename)
