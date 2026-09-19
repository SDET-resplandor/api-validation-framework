import sqlite3
from pathlib import Path
from unittest.mock import MagicMock
from urllib.parse import quote
 
import pytest
from fastapi.testclient import TestClient
 
from src.main import app
from src.dependencies import get_db
from src.sql_conect import NorthwindDatabase

TEST_API_KEY = "test-secret-key"
HEADERS = {"X-API-Key": TEST_API_KEY}
 
 
@pytest.fixture(autouse=True)
def mock_env_api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", TEST_API_KEY)
 
 
@pytest.fixture
def seeded_db_path(tmp_path: Path) -> Path:
    db_path = tmp_path / "northwind_test.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE Categories (
            CategoryID INTEGER PRIMARY KEY,
            CategoryName TEXT NOT NULL,
            Description TEXT
        );
        CREATE TABLE Suppliers (
            SupplierID INTEGER PRIMARY KEY,
            CompanyName TEXT NOT NULL
        );
        CREATE TABLE Products (
            ProductID INTEGER PRIMARY KEY,
            ProductName TEXT NOT NULL,
            SupplierID INTEGER,
            CategoryID INTEGER,
            QuantityPerUnit TEXT,
            UnitPrice REAL,
            UnitsInStock INTEGER,
            UnitsOnOrder INTEGER,
            ReorderLevel INTEGER,
            Discontinued INTEGER
        );
        INSERT INTO Categories (CategoryID, CategoryName, Description) VALUES
            (1, 'Beverages', 'Soft drinks, coffees, teas'),
            (2, 'Condiments', 'Sweet and savory sauces');
        INSERT INTO Suppliers (SupplierID, CompanyName) VALUES
            (1, 'Exotic Liquids'),
            (2, 'New Orleans Cajun Delights');
        INSERT INTO Products (
            ProductID, ProductName, SupplierID, CategoryID,
            QuantityPerUnit, UnitPrice, UnitsInStock, UnitsOnOrder, ReorderLevel, Discontinued
        ) VALUES
            (1, 'Chai', 1, 1, '10 boxes x 20 bags', 18.0, 39, 0, 10, 0),
            (2, 'Chang', 1, 1, '24 - 12 oz bottles', 19.0, 17, 40, 25, 0),
            (3, 'Aniseed Syrup', 2, 2, '12 - 550 ml bottles', 10.0, 13, 70, 25, 0);
        """
    )
    conn.commit()
    conn.close()
    return db_path
 
 
@pytest.fixture
def test_db(seeded_db_path: Path) -> NorthwindDatabase:
    return NorthwindDatabase(db_path=seeded_db_path)
 
 
@pytest.fixture
def client(test_db: NorthwindDatabase, monkeypatch) -> TestClient:
    monkeypatch.setattr("src.dependencies.db_instance", test_db)
    return TestClient(app)
 
 
class TestHealthCheck:
 
    def test_health_check_ok(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "Message": "The Northwind API works"}
 
    def test_health_check_db_uninitialized(self, monkeypatch):
        monkeypatch.setattr("src.dependencies.db_instance", None)
        response = TestClient(app).get("/")
        assert response.status_code == 503
 
    def test_health_check_ping_failure(self, monkeypatch):
        broken_db = MagicMock(spec=NorthwindDatabase)
        broken_db.ping.side_effect = RuntimeError("disk I/O error")
        monkeypatch.setattr("src.dependencies.db_instance", broken_db)
        response = TestClient(app).get("/")
        assert response.status_code == 503
 
 
class TestLifespan:
 
    def test_startup_fails_when_db_missing(self, monkeypatch):
        def raise_not_found(*args, **kwargs):
            raise FileNotFoundError("Couldn't find database at 'missing.db'")
 
        monkeypatch.setattr("src.dependencies.NorthwindDatabase", raise_not_found)
 
        with pytest.raises(FileNotFoundError):
            with TestClient(app):
                pass
 
    def test_startup_fails_when_api_key_missing(self, monkeypatch):
        monkeypatch.delenv("API_KEY", raising=False)
 
        with pytest.raises(RuntimeError):
            with TestClient(app):
                pass
 
 
class TestAuth:
 
    def test_missing_api_key_returns_401(self, client: TestClient):
        response = client.get("/api/v1/table/products")
        assert response.status_code == 401
 
    def test_invalid_api_key_returns_401(self, client: TestClient):
        response = client.get("/api/v1/table/products", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 401
 
    def test_empty_api_key_returns_401(self, client: TestClient):
        response = client.get("/api/v1/table/products", headers={"X-API-Key": ""})
        assert response.status_code == 401
 
    def test_valid_api_key_allows_access(self, client: TestClient):
        response = client.get("/api/v1/table/products", headers=HEADERS)
        assert response.status_code == 200
 
 
class TestTableEndpoint:
 
    def test_read_table_success(self, client: TestClient):
        response = client.get("/api/v1/table/products?limit=2", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert "ProductID" in data[0]
 
    def test_read_table_default_limit(self, client: TestClient):
        response = client.get("/api/v1/table/products", headers=HEADERS)
        assert response.status_code == 200
        assert len(response.json()) == 3
 
    def test_read_table_case_insensitive(self, client: TestClient):
        response = client.get("/api/v1/table/PRODUCTS", headers=HEADERS)
        assert response.status_code == 200
 
    def test_read_table_sql_injection_attempt_rejected(self, client: TestClient):
        malicious_table = "products; DROP TABLE Products;--"
        response = client.get(
            f"/api/v1/table/{quote(malicious_table, safe='')}", headers=HEADERS
        )
        assert response.status_code == 400
 
    @pytest.mark.parametrize("limit,expected_status", [
        (1, 200),
        (100, 200),
        (0, 422),
        (101, 422),
        (-5, 422),
    ])
    def test_read_table_limit_boundaries(self, client: TestClient, limit, expected_status):
        response = client.get(f"/api/v1/table/products?limit={limit}", headers=HEADERS)
        assert response.status_code == expected_status
 
    def test_read_table_internal_server_error_masking(self, client: TestClient):
        mock_db = MagicMock(spec=NorthwindDatabase)
        mock_db.get_table_data.side_effect = RuntimeError("Database connection dropped")
 
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            response = client.get("/api/v1/table/products", headers=HEADERS)
            assert response.status_code == 500
            assert response.json() == {"detail": "Internal server error."}
        finally:
            app.dependency_overrides.clear()
 
 
class TestCategoryEndpoint:
 
    def test_read_category_success(self, client: TestClient):
        response = client.get("/api/v1/categories/1", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["CategoryID"] == 1
        assert data["CategoryName"] == "Beverages"
 
    def test_read_category_not_found(self, client: TestClient):
        response = client.get("/api/v1/categories/999999", headers=HEADERS)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
 
    @pytest.mark.parametrize("category_id", ["abc", "1.5", "-1", "0"])
    def test_read_category_invalid_id_returns_422(self, client: TestClient, category_id):
        response = client.get(f"/api/v1/categories/{category_id}", headers=HEADERS)
        assert response.status_code == 422
 
 
class TestSuppliersEndpoint:
 
    def test_read_suppliers_success(self, client: TestClient):
        response = client.get("/api/v1/suppliers", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert {item["SupplierID"] for item in data} == {1, 2}
 
    @pytest.mark.parametrize("limit,expected_status", [
        (1, 200),
        (30, 200),
        (0, 422),
        (31, 422),
    ])
    def test_read_suppliers_limit_boundaries(self, client: TestClient, limit, expected_status):
        response = client.get(f"/api/v1/suppliers?limit={limit}", headers=HEADERS)
        assert response.status_code == expected_status
 
 
class TestProductEndpoint:
 
    def test_read_product_success(self, client: TestClient):
        response = client.get("/api/v1/products/1", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["ProductID"] == 1
        assert data["ProductName"] == "Chai"
 
    def test_read_product_response_contract(self, client: TestClient):
        response = client.get("/api/v1/products/1", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        expected_keys = {
            "ProductID", "ProductName", "SupplierID", "CategoryID",
            "QuantityPerUnit", "UnitPrice", "UnitsInStock",
            "UnitsOnOrder", "ReorderLevel", "Discontinued",
        }
        assert set(data.keys()) == expected_keys
        assert isinstance(data["ProductID"], int)
        assert isinstance(data["ProductName"], str)
        assert isinstance(data["UnitPrice"], (int, float))
 
    def test_read_product_not_found(self, client: TestClient):
        response = client.get("/api/v1/products/999999", headers=HEADERS)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
 
    @pytest.mark.parametrize("product_id", ["abc", "1.5", "-1", "0"])
    def test_read_product_invalid_id_returns_422(self, client: TestClient, product_id):
        response = client.get(f"/api/v1/products/{product_id}", headers=HEADERS)
        assert response.status_code == 422
 
    def test_read_product_internal_server_error_masking(self, client: TestClient):
        mock_db = MagicMock(spec=NorthwindDatabase)
        mock_db.get_product_by_id.side_effect = RuntimeError("disk I/O error")
 
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            response = client.get("/api/v1/products/1", headers=HEADERS)
            assert response.status_code == 500
            assert response.json() == {"detail": "Internal server error."}
        finally:
            app.dependency_overrides.clear()
 
 
class TestRoutingContract:
 
    def test_unknown_route_returns_404(self, client: TestClient):
        response = client.get("/api/v1/unknown", headers=HEADERS)
        assert response.status_code == 404
 
    def test_method_not_allowed_on_products(self, client: TestClient):
        response = client.post("/api/v1/products/1", headers=HEADERS)
        assert response.status_code == 405
        
class TestResponseContracts:

    def test_category_response_contract(self, client: TestClient):
        response = client.get("/api/v1/categories/1", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()

        expected_keys = {"CategoryID", "CategoryName", "Description"}
        assert set(data.keys()) == expected_keys
        assert isinstance(data["CategoryID"], int)
        assert isinstance(data["CategoryName"], str)
        assert data["Description"] is None or isinstance(data["Description"], str)

    def test_supplier_response_contract(self, client: TestClient):
        response = client.get("/api/v1/suppliers", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) > 0

        expected_keys = {"SupplierID", "CompanyName"}
        for supplier in data:
            assert set(supplier.keys()) == expected_keys
            assert isinstance(supplier["SupplierID"], int)
            assert isinstance(supplier["CompanyName"], str)

    def test_table_endpoint_returns_raw_dict_structure(self, client: TestClient):
        
        response = client.get("/api/v1/table/products?limit=1", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()[0]

        assert "ProductID" in data
        assert "ProductName" in data