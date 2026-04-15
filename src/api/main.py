from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from src.services.pdf_processor import is_pdf, get_file_hash, extract_text

from src.services.ai_service import process_summary_task
from src.repository.pdf_repository import PDFRepository
from src.models.pdf import ProcessResult, DocumentMetadata
import uvicorn

app = FastAPI(title="PDF ExtraText AI")

pdf_repo = PDFRepository()

@app.post("/upload")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not is_pdf(file.filename):
        raise HTTPException(status_code=400, detail="El archivo no es un PDF válido ❌")
    
    content = await file.read()
    file_hash = get_file_hash(content)
    
    existing = await pdf_repo.get_by_hash(file_hash)
    if existing:
        return {
            "status": existing.status,
            "message": "Información recuperada de la base de datos ✅",
            "data": existing
        }
    
    try:
        texto_final = extract_text(content)
        
        metadata = DocumentMetadata(
            filename=file.filename,
            page_count=0, # Esto se puede calcular después con una librería
            file_size=len(content)
        )
        
        initial_process = ProcessResult(
            file_hash=file_hash,
            status="processing",
            metadata=metadata
        )
        
        await pdf_repo.save(initial_process)
        
        background_tasks.add_task(process_summary_task, texto_final, file_hash, pdf_repo)
        
        return {
            "status": "processing",
            "message": "Archivo recibido y registrado. Procesando con IA... ⏳",
            "data": {
                "filename": file.filename,
                "hash": file_hash
            }
        }
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error: {str(e)} ⚠️")

@app.get("/status/{file_hash}")
async def get_status(file_hash: str):

    resultado = await pdf_repo.get_by_hash(file_hash)
    
    if resultado is None:
        raise HTTPException(status_code=404, detail="No se encontró procesamiento para este hash.")
    
    # Si está en 'processing', el modelo ya trae ese status por defecto
    return {
        "status": resultado.status,
        "hash": file_hash,
        "data": resultado
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)