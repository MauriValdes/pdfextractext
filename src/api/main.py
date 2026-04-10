from fastapi import FastAPI, File, UploadFile, HTTPException
from src.services.pdf_processor import is_pdf, get_file_hash, extract_text

app = FastAPI()

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    # 1. Validación rápida: ¿Es un PDF por su nombre? 📛
    if not is_pdf(file.filename):
        raise HTTPException(
            status_code=400, 
            detail="El archivo no es un PDF válido ❌"
        )
    
    # 2. Leemos los bytes del archivo 📖
    # Usamos await porque la lectura es una operación asíncrona en FastAPI
    content = await file.read()
    
    # 3. Generamos la huella digital (Hash SHA-256) 🧬
    # Esto le servirá a tu compañero para la base de datos
    file_hash = get_file_hash(content)
    
    # 4. Intentamos extraer el texto 🛠️
    try:
        texto_final = extract_text(content)
        
        # 5. Respuesta final de éxito ✅
        # Aquí agrupamos toda la información útil
        return {
            "status": "success",
            "message": "Archivo procesado correctamente",
            "data": {
                "filename": file.filename,
                "hash": file_hash,
                "text": texto_final
            }
        }
        
    except Exception as e:
        # Si algo falla en la extracción (archivo corrupto, etc.)
        # Enviamos un error específico como querías
        raise HTTPException(
            status_code=422, 
            detail=f"No se pudo procesar el contenido del PDF: {str(e)} ⚠️"
        )
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)