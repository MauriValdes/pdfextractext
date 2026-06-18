from fastapi import APIRouter, UploadFile, File, HTTPException, status
from src.database.mongodb import db_connection
from src.services.pdf_service import extract_text_from_pdf, get_pdf_checksum
from src.models.document import DocumentCreate
from src.config.config import settings

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_pdf(file: UploadFile = File(...)):

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="El archivo debe ser un PDF"
        )

    pdf_bytes = await file.read()
    max_size_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(pdf_bytes) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"El archivo es demasiado grande (máximo {settings.max_file_size_mb}MB)"
        )

    checksum = get_pdf_checksum(pdf_bytes)
    db = db_connection.db
    
    existing_doc = await db["processed_pdfs"].find_one({"checksum": checksum})
    if existing_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Este documento ya ha sido procesado anteriormente"
        )

    try:
        text_content = extract_text_from_pdf(pdf_bytes)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Error al extraer texto del PDF"
        )

    new_doc = DocumentCreate(
        filename=file.filename,
        content=text_content,
        checksum=checksum,
        size_bytes=len(pdf_bytes)
    )

    await db["processed_pdfs"].insert_one(new_doc.model_dump())

    return {
        "message": "Archivo recibido y procesado exitosamente", 
        "filename": file.filename
    }