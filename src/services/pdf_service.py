import fitz  # PyMuPDF
import io

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    # Extrae el contenido de texto de un archivo PDF procesado en memoria.
    with fitz.open(stream=io.BytesIO(pdf_bytes), filetype="pdf") as doc:
        text = ""
        for page in doc:
            text += page.get_text()
            
    return text