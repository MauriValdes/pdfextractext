from src.models.document import DocumentCreate
from src.config.config import settings

class DocumentRepository:
    def __init__(self, db):
        self.db = db
        self.collection = db[settings.mongo_collection]

    async def find_by_checksum(self, checksum: str) -> dict | None:
        """Busca un documento en la base de datos por su hash único."""
        
        document = await self.collection.find_one({"checksum": checksum})
        return document

    async def save_document(self, document_data: DocumentCreate) -> str:
        """Guarda un documento procesado en MongoDB y retorna su ID."""

        doc_dict = document_data.model_dump()
        result = await self.collection.insert_one(doc_dict)
        return str(result.inserted_id)