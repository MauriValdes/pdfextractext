import ollama
import os

# 🌐 Configuración desde Docker
OLLAMA_HOST = os.getenv("OLLAMA_URL", "http://ollama:11434")

# 🧠 Base de datos temporal en memoria
results_db = {}

async def process_summary_task(text: str, file_hash: str):
    """
    Tarea de fondo optimizada para 8GB de RAM. 
    Limpia el texto para evitar respuestas vacías en modelos pequeños.
    """
    # 🛠️ Cliente con timeout infinito
    client = ollama.AsyncClient(host=OLLAMA_HOST, timeout=None)
    
    try:
        results_db[file_hash] = "PROCESANDO..."
        print(f"--- 🚀 Iniciando IA para hash: {file_hash} ---")

        # 1. Limpieza de texto (Crucial para TinyDolphin)
        # Quitamos saltos de línea extra y limitamos a 2500 caracteres
        clean_text = " ".join(text.split())[:2500]

        # 2. Prompt simplificado
        prompt = (
            "Summarize the following text in 3 key points. "
            "Write in Spanish:\n\n"
            f"{clean_text}"
        )
        
        # 3. Generación con parámetros de bajo consumo
        response = await client.generate(
            model='tinydolphin', 
            prompt=prompt,
            options={
                "num_ctx": 1024,   # Contexto pequeño = Menos RAM
                "num_thread": 2,   # No saturamos todos los núcleos de la notebook
                "temperature": 0.1 # Menos creatividad, más precisión
            }
        )
        
        resumen = response.get('response', '').strip()

        # 4. Verificación de respuesta vacía
        if not resumen:
            resumen = "La IA procesó el archivo pero no pudo generar un resumen. Intentá con un texto más corto."

        # 💾 Guardamos resultado
        results_db[file_hash] = resumen
        print(f"✅ Procesamiento finalizado para: {file_hash}")

    except Exception as e:
        error_msg = f"❌ Error en la tarea de IA: {str(e)}"
        results_db[file_hash] = error_msg
        print(error_msg)