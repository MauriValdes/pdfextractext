import fitz  # PyMuPDF
import io
import hashlib

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    # Extrae el contenido de texto de un archivo PDF procesado en memoria.
    with fitz.open(stream=io.BytesIO(pdf_bytes), filetype="pdf") as doc:
        text = ""
        for page in doc:
            text += page.get_text()
            
    return text

def get_pdf_checksum(pdf_bytes: bytes) -> str:
    # 1. Creamos el hash y le pasamos los bytes, luego pedimos el hexadecimal
    return hashlib.sha256(pdf_bytes).hexdigest()