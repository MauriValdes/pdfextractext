from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from typing import List

from src.database.mongodb import db_connection
from src.repository.document_repository import DocumentRepository
from src.services import pdf_service 
from src.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


# 🛠️ Función auxiliar para convertir el _id (ObjectId) a string
def format_doc(doc: dict) -> dict:
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


# 💉 Inyección de Dependencias
def get_document_service() -> DocumentService:
    repository = DocumentRepository(db_connection.db)
    return DocumentService(repository=repository, pdf_service=pdf_service)


# 1. CREATE: Subir y procesar un nuevo PDF 📄
@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service)
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser un PDF"
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío"
        )

    try:
        doc = await service.process_pdf(file_bytes=file_bytes, filename=file.filename)
        return {
            "message": "Archivo recibido y procesado exitosamente",
            "document": format_doc(doc)  # 👈 Formateamos el id aquí
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al procesar el PDF"
        )


# 2. READ: Obtener todos los documentos 📚
@router.get("", status_code=status.HTTP_200_OK)
async def get_all_documents(
    service: DocumentService = Depends(get_document_service)
):
    documents = await service.get_all_documents()
    # 👈 Formateamos cada documento de la lista
    return [format_doc(doc) for doc in documents]


# 3. READ: Obtener un documento por ID 🔍
@router.get("/{document_id}", status_code=status.HTTP_200_OK)
async def get_document_by_id(
    document_id: str,
    service: DocumentService = Depends(get_document_service)
):
    doc = await service.get_document_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    return format_doc(doc)  # 👈 Formateamos el id aquí


# 4. DELETE: Borrar un documento por ID 🗑️
@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document_by_id(
    document_id: str,
    service: DocumentService = Depends(get_document_service)
):
    try:
        await service.delete_document(document_id)
        return {"message": "Documento eliminado exitosamente"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )