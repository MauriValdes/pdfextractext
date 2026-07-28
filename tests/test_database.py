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

@pytest.mark.asyncio
async def test_find_all_documents():
    # 1. Arrange (Preparar) 🛠️
    await db_connection.connect(settings.mongo_db_test)
    repository = DocumentRepository(db_connection.db)
    
    doc1 = DocumentCreate(filename="doc1.pdf", content="Texto 1", checksum="hash_111", size_bytes=100)
    doc2 = DocumentCreate(filename="doc2.pdf", content="Texto 2", checksum="hash_222", size_bytes=200)
    
    await repository.save_document(doc1)
    await repository.save_document(doc2)

    # 2. Act (Actuar) ⚡
    documents = await repository.find_all()

    # 3. Assert (Verificar) 🔍
    assert len(documents) >= 2
    filenames = [d["filename"] for d in documents]
    assert "doc1.pdf" in filenames
    assert "doc2.pdf" in filenames

    # 4. Teardown (Limpieza) 🧹
    await repository.collection.delete_many({"checksum": {"$in": ["hash_111", "hash_222"]}})
    await db_connection.close()


@pytest.mark.asyncio
async def test_delete_by_id():
    # 1. Arrange (Preparar) 🛠️
    await db_connection.connect(settings.mongo_db_test)
    repository = DocumentRepository(db_connection.db)
    
    # Limpiamos basura previa antes de probar 🧹
    await repository.collection.delete_many({"checksum": "hash_del"})
    
    doc = DocumentCreate(filename="para_borrar.pdf", content="Texto borrable", checksum="hash_del", size_bytes=150)
    inserted_id = await repository.save_document(doc)

    # 2. Act (Actuar) ⚡
    deleted_count = await repository.delete_by_id(inserted_id)
    found_doc = await repository.find_by_checksum("hash_del")

    # 3. Assert (Verificar) 🔍
    assert deleted_count == 1
    assert found_doc is None

    # 4. Teardown (Limpieza) 🧹
    await db_connection.close()