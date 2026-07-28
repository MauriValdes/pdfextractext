import pytest
import io
import fitz 
from httpx import AsyncClient, ASGITransport
from src.main import app 
from src.database.mongodb import db_connection


@pytest.fixture
async def client():
    # 1. Conexión y limpieza antes de la prueba 🧹
    await db_connection.connect()
    await db_connection.db["processed_pdfs"].delete_many({}) 
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    # 2. Cierre de conexión al finalizar 🔒
    await db_connection.close()


@pytest.mark.asyncio
async def test_upload_pdf_and_verify_in_db(client: AsyncClient):
    # 1. Arrange: Crear un PDF válido en memoria 📄
    doc = fitz.open() 
    page = doc.new_page() 
    text_to_test = "Este es un texto de prueba para el test de integracion."
    page.insert_text((50, 50), text_to_test)
    
    pdf_buffer = io.BytesIO()
    doc.save(pdf_buffer)
    file_content = pdf_buffer.getvalue() 
    doc.close()

    files = {"file": ("test_generado.pdf", file_content, "application/pdf")}
    
    # 2. Act: Enviar la petición POST ⚡
    response = await client.post("/documents/upload", files=files)
    
    # 3. Assert: Verificar status HTTP y persistencia en la BD 🔍
    assert response.status_code == 201
    
    db = db_connection.db
    doc_in_db = await db["processed_pdfs"].find_one({"filename": "test_generado.pdf"})
    
    assert doc_in_db is not None
    assert text_to_test in doc_in_db["content"]


@pytest.mark.asyncio
async def test_get_all_documents(client: AsyncClient):
    # 1. Arrange: Insertar datos de prueba directos 🛠️
    db = db_connection.db
    await db["processed_pdfs"].insert_many([
        {"filename": "doc_a.pdf", "content": "Texto A", "checksum": "hash_a", "size_bytes": 100},
        {"filename": "doc_b.pdf", "content": "Texto B", "checksum": "hash_b", "size_bytes": 200},
    ])

    # 2. Act: Enviar la petición GET ⚡
    response = await client.get("/documents")

    # 3. Assert: Verificar status 200 y contenido de la lista 🔍
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    filenames = [doc["filename"] for doc in data]
    assert "doc_a.pdf" in filenames
    assert "doc_b.pdf" in filenames


@pytest.mark.asyncio
async def test_delete_document_by_id(client: AsyncClient):
    # 1. Arrange: Insertar un documento para luego borrarlo 🛠️
    db = db_connection.db
    insert_result = await db["processed_pdfs"].insert_one({
        "filename": "borrar_me.pdf",
        "content": "Texto borrable",
        "checksum": "hash_borrar",
        "size_bytes": 150
    })
    doc_id = str(insert_result.inserted_id)

    # 2. Act: Enviar la petición DELETE ⚡
    response = await client.delete(f"/documents/{doc_id}")

    # 3. Assert: Verificar status 200 y que ya no exista en la BD 🔍
    assert response.status_code == 200
    
    doc_in_db = await db["processed_pdfs"].find_one({"_id": insert_result.inserted_id})
    assert doc_in_db is None