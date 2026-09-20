from fastapi.testclient import TestClient


class TestRoutingContract:
    def test_unknown_route_returns_404(self, client: TestClient):
        response = client.get("/api/v1/unknown")
        assert response.status_code == 404

    def test_method_not_allowed_on_products(self, client: TestClient):
        response = client.post("/api/v1/products/1")
        assert response.status_code == 405
