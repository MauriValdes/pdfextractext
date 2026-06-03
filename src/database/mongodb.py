from motor.motor_asyncio import AsyncIOMotorClient
from src.config.config import settings

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self, database_name: str = None):
        """
        Conecta a MongoDB. Si se especifica database_name, usa esa base de datos (para tests).
        Si no se especifica, usa la de desarrollo por defecto.
        """
        self.client = AsyncIOMotorClient(settings.mongo_url)
        
        # 🔄 Selección dinámica de la base de datos
        if database_name:
            self.db = self.client[database_name]
        else:
            self.db = self.client[settings.mongo_db_dev]
            
        print(f"Conectado a MongoDB en la base de datos: {self.db.name}")

    async def close(self):
        if self.client:
            self.client.close()

db_connection = MongoDB()