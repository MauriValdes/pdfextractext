import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.document_service import DocumentService


@pytest.mark.asyncio
async def test_process_pdf_success_saves_document():
    # 1. Mocks
    mock_repo = AsyncMock()
    mock_repo.find_by_checksum.return_value = None  # No es duplicado
    mock_repo.save_document.return_value = {"id": "123", "filename": "manual.pdf"}

    mock_pdf_service = MagicMock()
    mock_pdf_service.get_pdf_checksum.return_value = "12345"
    mock_pdf_service.extract_text_from_pdf.return_value = "texto del pdf"

    # 2. Instanciamos el servicio con ambas dependencias
    service = DocumentService(repository=mock_repo, pdf_service=mock_pdf_service)

    fake_bytes = b"%PDF-content"
    filename = "manual.pdf"

    # 3. Llamada al orquestador
    result = await service.process_pdf(fake_bytes, filename)

    # 4. Aserciones
    mock_pdf_service.get_pdf_checksum.assert_called_once_with(fake_bytes)
    mock_pdf_service.extract_text_from_pdf.assert_called_once_with(fake_bytes)
    mock_repo.find_by_checksum.assert_called_once_with("12345")
    mock_repo.save_document.assert_called_once()
    assert result == {"id": "123", "filename": "manual.pdf"}


@pytest.mark.asyncio
async def test_process_pdf_raises_error_if_duplicate():
    mock_repo = AsyncMock()
    mock_repo.find_by_checksum.return_value = {"filename": "manual.pdf"}  # SÍ existe

    mock_pdf_service = MagicMock()
    mock_pdf_service.get_pdf_checksum.return_value = "12345"

    service = DocumentService(repository=mock_repo, pdf_service=mock_pdf_service)

    fake_bytes = b"%PDF-content"

    # Verificamos la excepción de duplicado
    with pytest.raises(ValueError, match="El documento ya existe"):
        await service.process_pdf(fake_bytes, "manual.pdf")

    # Verificamos que NUNCA intentó extraer texto ni guardar si era duplicado
    mock_pdf_service.extract_text_from_pdf.assert_not_called()
    mock_repo.save_document.assert_not_called()


@pytest.mark.asyncio
async def test_get_all_documents_calls_repo():
    mock_repo = AsyncMock()
    mock_repo.find_all.return_value = [{"id": "1"}, {"id": "2"}]

    service = DocumentService(repository=mock_repo, pdf_service=MagicMock())

    result = await service.get_all_documents()

    mock_repo.find_all.assert_called_once()
    assert len(result) == 2


@pytest.mark.asyncio
async def test_delete_document_success_if_exists():
    mock_repo = AsyncMock()
    mock_repo.delete_by_id.return_value = True

    service = DocumentService(repository=mock_repo, pdf_service=MagicMock())

    result = await service.delete_document("123")

    mock_repo.delete_by_id.assert_called_once_with("123")
    assert result is True

@pytest.mark.asyncio
async def test_delete_document_raises_error_if_not_found():
    mock_repo = AsyncMock()
    # Simulamos que el repo no encontró el ID y devolvió False
    mock_repo.delete_by_id.return_value = False

    service = DocumentService(repository=mock_repo, pdf_service=MagicMock())

    with pytest.raises(ValueError, match="El documento no existe"):
        await service.delete_document("id_inexistente")

    mock_repo.delete_by_id.assert_called_once_with("id_inexistente")