from fastapi.testclient import TestClient
from src.main import app

# Test client for our FastAPI app
client = TestClient(app)

def test_read_root():
    """Checks that the root endpoint responds correctly (Health Check)."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Northwind API is running."}

def test_read_table_success():
    """Checks that records can be fetched from an existing table (e.g. Customers)."""
    response = client.get("/api/v1/table/Customers?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 2

def test_read_customer_not_found():
    """Checks that the API returns a 404 error when the customer doesn't exist."""
    response = client.get("/api/v1/customers/FAKE_CUSTOMER_123")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]