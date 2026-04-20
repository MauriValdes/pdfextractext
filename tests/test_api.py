from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_upload_pdf_success():
    # 1. Preparamos un "archivo" PDF ficticio
    file_content = b"%PDF-1.4 dummy content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    
    # 2. Ejecutamos la acción
    response = client.post("/documents/upload", files=files)
    
    # 3. Verificamos el resultado
    assert response.status_code == 201
    assert response.json()["message"] == "Archivo recibido exitosamente"