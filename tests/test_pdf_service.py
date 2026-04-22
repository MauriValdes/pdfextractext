import fitz
from src.services.pdf_service import extract_text_from_pdf

def create_mock_pdf_bytes() -> bytes:
    """Función auxiliar para generar un PDF real en memoria para las pruebas."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Texto de prueba")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def test_extract_text_from_pdf_success():
    # 1. Preparamos los datos de prueba
    pdf_content = create_mock_pdf_bytes()
    
    # 2. Ejecutamos la acción
    result = extract_text_from_pdf(pdf_content)
    
    # 3. Verificamos el resultado
    assert isinstance(result, str)
    assert "Texto de prueba" in result