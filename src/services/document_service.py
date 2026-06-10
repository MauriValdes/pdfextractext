from src.repository.document_repository import DocumentRepository

class DocumentService:
    def __init__(self, repository: DocumentRepository):
        # Guardamos la dependencia inyectada
        self.repository = repository

    async def process_new_document(self, document_data):
        # 1. Buscamos si ya existe el documento por su checksum
        existing_doc = await self.repository.find_by_checksum(document_data.checksum)
        
        # 2. Si existe (no es None), lanzamos el error para detener el proceso
        if existing_doc is not None:
            raise ValueError("El documento ya existe")
            
        # 3. Si no existe, procedemos a guardarlo
        await self.repository.save_document(document_data)