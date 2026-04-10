from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from src.services.pdf_processor import is_pdf, get_file_hash, extract_text
# 📥 Importamos la tarea Y el diccionario temporal
from src.services.ai_service import process_summary_task, results_db
import uvicorn

app = FastAPI(title="PDF ExtraText AI")

@app.post("/upload")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not is_pdf(file.filename):
        raise HTTPException(status_code=400, detail="El archivo no es un PDF válido ❌")
    
    content = await file.read()
    file_hash = get_file_hash(content)
    
    try:
        texto_final = extract_text(content)
        
        # 🚀 Disparamos la tarea diferida
        background_tasks.add_task(process_summary_task, texto_final, file_hash)
        
        return {
            "status": "processing",
            "message": "Archivo recibido. Usá el hash para consultar el estado.",
            "data": {
                "filename": file.filename,
                "hash": file_hash
            }
        }
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error: {str(e)} ⚠️")

# 🔍 NUEVO: Endpoint para consultar el resultado
@app.get("/status/{file_hash}")
async def get_status(file_hash: str):
    # Buscamos en la memoria temporal
    resumen = results_db.get(file_hash)
    
    if resumen is None:
        raise HTTPException(status_code=404, detail="No se encontró procesamiento para este hash.")
    
    if resumen == "PROCESANDO...":
        return {"status": "pending", "message": "La IA todavía está trabajando... ⏳"}
    
    return {
        "status": "completed",
        "hash": file_hash,
        "summary": resumen
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)