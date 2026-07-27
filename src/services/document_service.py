from src.repository.document_repository import DocumentRepository
from src.models.document import DocumentCreate


class DocumentService:
    def __init__(self, repository: DocumentRepository, pdf_service):
        self.repository = repository
        self.pdf_service = pdf_service

    async def process_pdf(self, file_bytes: bytes, filename: str):
        # 1. Calcular el checksum a través de pdf_service
        checksum = self.pdf_service.get_pdf_checksum(file_bytes)

        # 2. Verificar si el documento ya existe por su checksum
        existing_doc = await self.repository.find_by_checksum(checksum)
        if existing_doc is not None:
            raise ValueError("El documento ya existe")

        # 3. Extraer el contenido de texto del PDF
        content = self.pdf_service.extract_text_from_pdf(file_bytes)

        # 4. Instanciar el modelo DocumentCreate con los datos procesados
        document_data = DocumentCreate(
            filename=filename,
            content=content,
            checksum=checksum,
            size_bytes=len(file_bytes)
        )

        # 5. Guardar el documento en la BD
        return await self.repository.save_document(document_data)

    async def get_all_documents(self):
        """Obtiene la lista completa de documentos."""
        return await self.repository.find_all()

    async def delete_document(self, doc_id: str):
        """Elimina un documento por su ID validando si existe."""
        # Si delete_by_id devuelve False o None cuando no encuentra el documento:
        deleted = await self.repository.delete_by_id(doc_id)
        if not deleted:
            raise ValueError("El documento no existe")
        return True