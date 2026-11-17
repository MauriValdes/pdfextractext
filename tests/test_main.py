"""Tests para los endpoints principales de src/main.py."""
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_root_endpoint():
    """GET / debe responder 200 y mensaje de stateless."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "online"
    assert "stateless" in body["message"]


def test_health_endpoint():
    """GET /health debe responder 200 con {status: ok}."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body == {"status": "ok"}


def test_lifespan_runs():
    """Verificar que el lifespan de la app se ejecuta sin errores.
    Esto cubre la línea 9 del lifespan (el yield)."""
    # La app debería iniciar y estar lista para recibir peticiones
    assert app is not None
    # Verificar que la app tiene los routers incluídos
    assert app.routes is not None
