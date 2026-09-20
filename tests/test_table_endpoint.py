from unittest.mock import MagicMock
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.sql_connect import NorthwindDatabase
from tests.conftest import HEADERS


class TestProtectedTableEndpoint:
    def test_missing_api_key_returns_401(self, client: TestClient):
        response = client.get("/api/v1/table/employees")
        assert response.status_code == 401

    def test_invalid_api_key_returns_401(self, client: TestClient):
        response = client.get("/api/v1/table/employees", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 401

    def test_empty_api_key_returns_401(self, client: TestClient):
        response = client.get("/api/v1/table/employees", headers={"X-API-Key": ""})
        assert response.status_code == 401

    def test_valid_key_returns_full_table(self, client: TestClient):
        response = client.get("/api/v1/table/employees", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert "LastName" in data[0]

    def test_filter_by_id(self, client: TestClient):
        response = client.get("/api/v1/table/employees?id=1", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["EmployeeID"] == 1

    def test_filter_by_name(self, client: TestClient):
        response = client.get("/api/v1/table/shippers?name=speedy", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["ShipperName"] == "Speedy Express"

    def test_filter_by_name_on_table_without_name_column_fails(self, client: TestClient):
        response = client.get("/api/v1/table/orders?name=anything", headers=HEADERS)
        assert response.status_code == 400
        assert "does not support filtering by name" in response.json()["detail"]

    def test_access_customers_table(self, client: TestClient):
        response = client.get("/api/v1/table/customers", headers=HEADERS)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_access_orders_table_filtered_by_id(self, client: TestClient):
        response = client.get("/api/v1/table/orders?id=1", headers=HEADERS)
        assert response.status_code == 200
        assert response.json()[0]["OrderID"] == 1

    def test_forbidden_table(self, client: TestClient):
        response = client.get("/api/v1/table/sqlite_sequence", headers=HEADERS)
        assert response.status_code == 400
        assert "not an authorized table" in response.json()["detail"]

    def test_case_insensitive_table_name(self, client: TestClient):
        response = client.get("/api/v1/table/EMPLOYEES", headers=HEADERS)
        assert response.status_code == 200

    def test_sql_injection_attempt_rejected(self, client: TestClient):
        malicious = "employees; DROP TABLE Employees;--"
        response = client.get(f"/api/v1/table/{quote(malicious, safe='')}", headers=HEADERS)
        assert response.status_code == 400

    @pytest.mark.parametrize(
        "limit,expected_status",
        [
            (1, 200),
            (100, 200),
            (0, 422),
            (101, 422),
            (-5, 422),
        ],
    )
    def test_limit_boundaries(self, client: TestClient, limit, expected_status):
        response = client.get(f"/api/v1/table/employees?limit={limit}", headers=HEADERS)
        assert response.status_code == expected_status

    def test_internal_server_error_masking(self, client: TestClient):
        broken_db = MagicMock(spec=NorthwindDatabase)
        broken_db.get_table_data.side_effect = RuntimeError("Database connection dropped")
        app.state.db = broken_db
        try:
            response = client.get("/api/v1/table/employees", headers=HEADERS)
            assert response.status_code == 500
            assert response.json() == {"detail": "Internal server error."}
        finally:
            app.state.db = None
