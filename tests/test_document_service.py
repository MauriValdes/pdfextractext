import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.document_service import DocumentService
from src.models.document import DocumentCreate

@pytest.mark.asyncio
async def test_process_new_document_saves_if_not_duplicate():
    # 1. Mock del repositorio
    mock_repo = AsyncMock()
    # Simulamos que NO existe (find_by_checksum devuelve None)
    mock_repo.find_by_checksum.return_value = None
    
    # 2. Instanciamos el servicio
    service = DocumentService(repository=mock_repo)
    document_data = DocumentCreate(
    filename="manual.pdf",
    content="texto de prueba",
    checksum="12345",
    size_bytes=500)

    await service.process_new_document(document_data)
    
    # 4. Aserción: verificamos que se llamó a save_document
    mock_repo.save_document.assert_called_once()

@pytest.mark.asyncio
async def test_process_new_document_raises_error_if_duplicate():
    # 1. Mock: Simulamos que find_by_checksum SÍ devuelve algo (el duplicado)
    mock_repo = AsyncMock()
    # Aquí simulamos que el repositorio encuentra algo
    mock_repo.find_by_checksum.return_value = {"filename": "manual.pdf"} 
    
    service = DocumentService(repository=mock_repo)
    document_data = DocumentCreate(
        filename="manual.pdf",
        content="texto de prueba",
        checksum="12345",
        size_bytes=500
    )
    
    # 2. Verificamos que se lanza el ValueError
    with pytest.raises(ValueError, match="El documento ya existe"):
        await service.process_new_document(document_data)
        
    # 3. Verificamos que NUNCA se intentó guardar el duplicado
    mock_repo.save_document.assert_not_called()