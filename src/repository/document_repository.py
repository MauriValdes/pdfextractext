from src.models.document import DocumentCreate

class DocumentRepository:
    def __init__(self, db):
        self.db = db
        self.collection = db["processed_pdfs"]

    async def find_by_checksum(self, checksum: str) -> dict | None:
        """Busca un documento en la base de datos por su hash único."""
        document = await self.collection.find_one({"checksum": checksum})
        return document

    async def save_document(self, document_data: DocumentCreate) -> str:
        # 1. Convertimos el modelo de Pydantic a diccionario de Python 
        doc_dict = document_data.model_dump()
    
        # 2. Insertamos el diccionario en la colección de MongoDB 💾
        result = await self.collection.insert_one(doc_dict)
    
        # 3. Retornamos el ID único que generó la base de datos
        return str(result.inserted_id)