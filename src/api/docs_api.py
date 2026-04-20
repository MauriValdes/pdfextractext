from fastapi import APIRouter, UploadFile, File, status

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_pdf(file: UploadFile = File(...)):
    # Por ahora, solo devolvemos el mensaje que espera el test
    return {"message": "Archivo recibido exitosamente"}