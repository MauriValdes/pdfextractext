import fitz
from src.services.pdf_service import extract_text_from_pdf, get_pdf_checksum

def create_mock_pdf_bytes(text: str = "Texto de prueba") -> bytes:
    """Función auxiliar para generar un PDF real en memoria para las pruebas."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
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

def test_get_pdf_checksum_consistency():
    # 1. Preparamos los datos (mismos bytes para ambos)
    pdf_content = create_mock_pdf_bytes()
    
    # 2. Ejecutamos la acción dos veces
    checksum_1 = get_pdf_checksum(pdf_content)
    checksum_2 = get_pdf_checksum(pdf_content)
    
    # 3. Verificamos que sean idénticos
    assert isinstance(checksum_1, str)
    assert len(checksum_1) == 64  
    assert checksum_1 == checksum_2 

def test_get_pdf_checksum_uniqueness():
    # 1. Preparamos dos contenidos diferentes
    pdf_content_a = create_mock_pdf_bytes("Contenido A")
    pdf_content_b = create_mock_pdf_bytes("Contenido B")
    
    # 2. Ejecutamos la acción para ambos
    checksum_a = get_pdf_checksum(pdf_content_a)
    checksum_b = get_pdf_checksum(pdf_content_b)
    
    # 3. Verificamos que las huellas digitales sean distintas
    assert checksum_a != checksum_b