from fastapi.testclient import TestClient


class TestPublicSuppliers:
    def test_list_suppliers_no_key_required(self, client: TestClient):
        response = client.get("/api/v1/suppliers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_suppliers_only_expose_id_and_name(self, client: TestClient):
        response = client.get("/api/v1/suppliers")
        data = response.json()
        for supplier in data:
            assert set(supplier.keys()) == {"SupplierID", "SupplierName"}

    def test_list_suppliers_limit_boundaries(self, client: TestClient):
        assert client.get("/api/v1/suppliers?limit=1").status_code == 200
        assert client.get("/api/v1/suppliers?limit=0").status_code == 422
        assert client.get("/api/v1/suppliers?limit=31").status_code == 422
