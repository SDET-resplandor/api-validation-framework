from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.sql_connect import NorthwindDatabase


class TestHealthCheck:
    def test_health_check_ok(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "Message": "The Northwind API works"}

    def test_health_check_db_uninitialized(self):
        app.state.db = None
        response = TestClient(app).get("/")
        assert response.status_code == 503

    def test_health_check_ping_failure(self):
        broken_db = MagicMock(spec=NorthwindDatabase)
        broken_db.ping.side_effect = RuntimeError("disk I/O error")
        app.state.db = broken_db
        response = TestClient(app).get("/")
        assert response.status_code == 503


class TestLifespan:
    def test_startup_fails_when_db_missing(self, monkeypatch):
        def raise_not_found(*args, **kwargs):
            raise FileNotFoundError("Couldn't find database at 'missing.db'")

        monkeypatch.setattr("src.main.NorthwindDatabase", raise_not_found)

        with pytest.raises(FileNotFoundError), TestClient(app):
            pass

    def test_startup_fails_when_api_key_missing(self, monkeypatch):
        monkeypatch.delenv("API_KEY", raising=False)

        with pytest.raises(RuntimeError), TestClient(app):
            pass
