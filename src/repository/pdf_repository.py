from src.models.pdf import ProcessResult
from motor.motor_asyncio import AsyncIOMotorClient 

class PDFRepository:
    def __init__(self):

        mongo_url = os.getenv("MONGO_URL", "mongodb://db:27017")
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client["pdf_database"]
        self.collection = self.db["results"]

    async def get_by_hash(self, file_hash: str):
        document = await self.collection.find_one({"file_hash": file_hash})
        if document:
            return ProcessResult(**document)
        return None

    async def save(self, result: ProcessResult):
        # Convertimos el modelo a un diccionario para que Mongo lo entienda
        await self.collection.insert_one(result.model_dump())

    async def update_status(self, file_hash: str, update_data: dict):
        """
        Busca un documento por su hash y actualiza solo los campos
        que le enviemos en el diccionario update_data.
        """
        await self.collection.update_one(
            {"file_hash": file_hash},
            {"$set": update_data}
        )