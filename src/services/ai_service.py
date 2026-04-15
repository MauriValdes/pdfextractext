import ollama
import os
from src.repository.pdf_repository import PDFRepository

# 🌐 Configuración desde Docker
OLLAMA_HOST = os.getenv("OLLAMA_URL", "http://ollama:11434")


async def process_summary_task(text: str, file_hash: str, repo: PDFRepository):
    """
    Tarea de fondo que ahora persiste los resultados en MongoDB.
    """
    client = ollama.AsyncClient(host=OLLAMA_HOST, timeout=None)
    
    try:

        print(f"--- 🚀 Iniciando IA para hash: {file_hash} ---")

        clean_text = " ".join(text.split())[:2500]

        prompt = (
            "Summarize the following text in 3 key points. "
            "Write in Spanish:\n\n"
            f"{clean_text}"
        )
        
        response = await client.generate(
            model='tinydolphin', 
            prompt=prompt,
            options={
                "num_ctx": 1024,
                "num_thread": 2,
                "temperature": 0.1
            }
        )
        
        resumen = response.get('response', '').strip()

        if not resumen:
            resumen = "La IA procesó el archivo pero no pudo generar un resumen."

        update_data = {
            "status": "completed",
            "summary_text": resumen,
            "raw_text": text,      # Guardamos el texto extraído por si lo necesitamos luego
            "ai_model": "tinydolphin"
        }
        
        await repo.update_status(file_hash, update_data)
        print(f"✅ MongoDB actualizado para: {file_hash}")

    except Exception as e:
        error_msg = f"❌ Error en la tarea de IA: {str(e)}"
    
        await repo.update_status(file_hash, {
            "status": "error",
            "summary_text": error_msg
        })
        print(error_msg)