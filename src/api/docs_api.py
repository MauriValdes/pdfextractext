from fastapi import APIRouter, UploadFile, File, HTTPException, status
import fitz
from src.config.config import settings
from src.services.pdf_service import extract_text_from_pdf, get_pdf_checksum
from src.repository.document_repository import DocumentRepository
from src.services.document_service import DocumentService
from src.database.mongodb import db_connection
from src.models.document import DocumentCreate

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_pdf(file: UploadFile = File(...)):

    # Validar que el archivo sea un PDF
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser un PDF"
        )

    pdf_bytes = await file.read()

    # Validar que el archivo no esté vacío
    if len(pdf_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío"
        )

    # Validar tamaño máximo permitido
    max_size_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(pdf_bytes) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El archivo es demasiado grande (máximo {settings.max_file_size_mb}MB)"
        )

    # Obtener checksum
    checksum = get_pdf_checksum(pdf_bytes)

    # Extraer texto y validar PDF
    try:
        text_content = extract_text_from_pdf(pdf_bytes)

    except fitz.FileDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo PDF es inválido o está dañado"
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al procesar el PDF"
        )

    # Validar que el PDF contenga texto
    if not text_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El PDF no contiene texto para procesar"
        )

    repository = DocumentRepository(db_connection.db)
    service = DocumentService(repository)

    new_doc = DocumentCreate(
        filename=file.filename,
        content=text_content,
        checksum=checksum,
        size_bytes=len(pdf_bytes)
    )

    try:
        await service.process_new_document(new_doc)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return {
        "message": "Archivo recibido y procesado exitosamente",
        "filename": file.filename
    }