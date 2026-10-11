import sqlite3

from fastapi.testclient import TestClient

from app.main import create_app


def test_readiness_and_persistence_across_restart(tmp_path):
    path = tmp_path / "routiq.sqlite3"
    with TestClient(create_app(path), base_url="http://127.0.0.1") as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/api/ready").json()['tracking_available'] is True
    with sqlite3.connect(path) as connection:
        connection.execute("INSERT INTO app_metadata VALUES ('restart_probe', 'persisted')")
    with TestClient(create_app(path), base_url="http://127.0.0.1") as client:
        assert client.get("/api/ready").status_code == 200
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT value FROM app_metadata WHERE key = 'restart_probe'").fetchone() == ("persisted",)


def test_missing_metadata_returns_public_error(tmp_path):
    path = tmp_path / "routiq.sqlite3"
    with TestClient(create_app(path), base_url="http://127.0.0.1") as client:
        with sqlite3.connect(path) as connection:
            connection.execute("DROP TABLE app_metadata")
        response = client.get("/api/ready")
        assert response.status_code == 503
        assert response.json() == {"status": "unavailable", "code": "STORAGE_UNAVAILABLE"}
