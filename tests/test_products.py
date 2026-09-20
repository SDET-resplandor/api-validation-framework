import pytest
from fastapi.testclient import TestClient


class TestPublicProducts:
    def test_list_products_no_key_required(self, client: TestClient):
        response = client.get("/api/v1/products")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["SupplierName"] == "Exotic Liquids"
        assert data[0]["CategoryName"] == "Beverages"

    def test_list_products_filter_by_name(self, client: TestClient):
        response = client.get("/api/v1/products?name=chai")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["ProductName"] == "Chai"

    def test_list_products_limit_boundaries(self, client: TestClient):
        assert client.get("/api/v1/products?limit=1").status_code == 200
        assert client.get("/api/v1/products?limit=0").status_code == 422
        assert client.get("/api/v1/products?limit=101").status_code == 422

    def test_get_product_by_id_success(self, client: TestClient):
        response = client.get("/api/v1/products/1")
        assert response.status_code == 200
        assert response.json()["ProductName"] == "Chai"

    def test_get_product_by_id_not_found(self, client: TestClient):
        response = client.get("/api/v1/products/999999")
        assert response.status_code == 404

    @pytest.mark.parametrize("product_id", ["abc", "1.5", "-1", "0"])
    def test_get_product_by_id_invalid(self, client: TestClient, product_id):
        response = client.get(f"/api/v1/products/{product_id}")
        assert response.status_code == 422
