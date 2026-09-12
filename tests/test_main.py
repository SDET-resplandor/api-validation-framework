from fastapi.testclient import TestClient
from src.main import app

# Inicializamos el cliente de pruebas para nuestra app de FastAPI
client = TestClient(app)

def test_read_root():
    """Valida que el endpoint principal responda correctamente (Health Check)."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "API Northwind activa y lista."}

def test_read_table_success():
    """Valida que se puedan consultar registros de una tabla existente (ej. Customers)."""
    response = client.get("/api/v1/table/Customers?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 2

def test_read_customer_not_found():
    """Valida que la API devuelva un error 404 si el cliente no existe."""
    response = client.get("/api/v1/customers/CLIENTE_FALSO_123")
    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"]