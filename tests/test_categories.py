import pytest
from fastapi.testclient import TestClient


class TestPublicCategories:
    def test_get_category_by_id_success(self, client: TestClient):
        response = client.get("/api/v1/categories/1")
        assert response.status_code == 200
        assert response.json()["CategoryName"] == "Beverages"

    def test_get_category_by_id_not_found(self, client: TestClient):
        response = client.get("/api/v1/categories/999999")
        assert response.status_code == 404

    @pytest.mark.parametrize("category_id", ["abc", "1.5", "-1", "0"])
    def test_get_category_by_id_invalid(self, client: TestClient, category_id):
        response = client.get(f"/api/v1/categories/{category_id}")
        assert response.status_code == 422
