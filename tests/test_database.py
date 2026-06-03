import pytest
from src.config.config import settings
from src.database.mongodb import db_connection
from src.repository.document_repository import DocumentRepository
from src.models.document import DocumentCreate

@pytest.mark.asyncio
async def test_insert_and_find_document():
    # 1. Arrange (Preparar)
    await db_connection.connect(settings.mongo_db_test)
    
    # Instanciamos el repositorio real pasándole la base de datos
    repository = DocumentRepository(db_connection.db)
    
    # Usamos el modelo real de Pydantic para crear los datos de prueba
    documento_ejemplo = DocumentCreate(
        filename="documento_universidad.pdf",
        content="Texto extraído de prueba para validar la base de datos.",
        checksum="sha256_mock_789xyz",
        size_bytes=1024
    )

    # 2. Act (Actuar)
    # Guardamos usando el método del repositorio
    inserted_id = await repository.save_document(documento_ejemplo)
    
    # Buscamos usando el método del repositorio
    found_doc = await repository.find_by_checksum("sha256_mock_789xyz")

    # 3. Assert (Verificar)
    assert found_doc is not None
    assert found_doc["filename"] == "documento_universidad.pdf"
    assert found_doc["checksum"] == "sha256_mock_789xyz"
    
    # 4. Teardown (Limpieza)
    # Limpiamos usando la colección interna del repositorio para no dejar rastro
    await repository.collection.delete_one({"checksum": "sha256_mock_789xyz"})
    await db_connection.close()