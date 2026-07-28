from bson import ObjectId
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

    async def find_all(self) -> list[dict]:
        """Obtiene todos los documentos almacenados en la colección."""
        cursor = self.collection.find({})
        documents = await cursor.to_list(length=None)
        return documents

    async def delete_by_id(self, document_id: str) -> int:
        """Elimina un documento por su ID de MongoDB y retorna la cantidad de eliminados."""
        result = await self.collection.delete_one({"_id": ObjectId(document_id)})
        return result.deleted_count