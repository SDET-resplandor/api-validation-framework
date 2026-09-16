from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest

from src.main import app, get_db
from src.sql_conect import NorthwindDatabase

@pytest.fixture
def client() -> TestClient:
    """Provides an isolated test client fixture for each test case."""
    return TestClient(app)

def test_health_check(client: TestClient):
    """Verifies service health and availability."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "Northwind API is running.",
    }

def test_read_table_success(client: TestClient):
    """Verifies successful retrieval from the authorized 'products' table respecting the limit."""
    response = client.get("/api/v1/table/products?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 2
    if data:
        # Validate dictionary key structure for product entities
        assert any(k.lower() == "productid" for k in data[0].keys())


def test_read_product_success(client: TestClient):
    """Verifies fetching an existing product by ID."""
    response = client.get("/api/v1/products/1")
    assert response.status_code == 200
    data = response.json()
    product_id = data.get("ProductID") or data.get("productid")
    assert str(product_id) == "1"


def test_read_table_forbidden_table(client: TestClient):
    """Verifies that unauthorized tables outside the whitelist return 400 Bad Request."""
    response = client.get("/api/v1/table/Employees")
    assert response.status_code == 400
    assert "not an authorized public table" in response.json()["detail"]


def test_read_table_invalid_limit_pydantic(client: TestClient):
    """Verifies out-of-range limit parameters (1-100) are caught by Pydantic validation (422)."""
    response_exceeded = client.get("/api/v1/table/products?limit=150")
    assert response_exceeded.status_code == 422

    response_negative = client.get("/api/v1/table/products?limit=0")
    assert response_negative.status_code == 422


def test_read_product_not_found(client: TestClient):
    """Verifies a 404 Not Found response when querying a non-existent product ID."""
    response = client.get("/api/v1/products/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_read_table_internal_server_error_masking(client: TestClient):
    """Injects a mock simulating a critical DB failure and verifies FastAPI

    returns 500 while masking sensitive internal errors.
    """
    mock_db = MagicMock(spec=NorthwindDatabase)
    mock_db.get_table_data.side_effect = RuntimeError(
        "Database connection dropped"
    )

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/v1/table/products")
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error."}
    finally:
        app.dependency_overrides.clear()