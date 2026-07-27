from src.repository.document_repository import DocumentRepository
from src.models.document import DocumentCreate

class DocumentService:
    def __init__(self, repository: DocumentRepository):
        self.repository = repository

    async def process_new_document(self, document_data: DocumentCreate):
        # Verificar si el documento ya existe
        existing_doc = await self.repository.find_by_checksum(document_data.checksum)

        if existing_doc is not None:
            raise ValueError("El documento ya existe")

        # Guardar el documento
        return await self.repository.save_document(document_data)