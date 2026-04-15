import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

# Este decorador permite usar fixtures asíncronos
@pytest.fixture(scope="session")
def event_loop():
    """Crea una instancia del loop de eventos para toda la sesión de tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db_client():
    """Configura un cliente de MongoDB para los tests."""
    # Usamos localhost porque el test corre desde tu máquina hacia el contenedor
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    yield client
    client.close()

@pytest.fixture
async def db(test_db_client):
    """Proporciona una base de datos limpia para cada test."""
    db_name = "pdf_test_db"  # Base de datos distinta a la real
    yield test_db_client[db_name]
    # Opcional: Limpiar la base de datos después de cada test
    await test_db_client.drop_database(db_name)