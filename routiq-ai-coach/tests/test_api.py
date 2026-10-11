from fastapi.testclient import TestClient
import pytest

from app.api.chat import Principal, authenticated_principal
from app.main import create_app

VALID = {"message": "How was my week?", "context": {"screen": "PROGRESS"}}


def test_health_and_default_auth_denial():
    with TestClient(create_app()) as client:
        assert client.get("/health").json()["live_ai_enabled"] is False
        assert client.get("/ready").json()["chat_available"] is False
        for headers in ({}, {"Authorization": "Bearer fake", "X-User-Id": "victim"}):
            assert client.post("/api/v1/ai/chat", json=VALID, headers=headers).status_code == 401


def authorized_app():
    app = create_app()
    app.dependency_overrides[authenticated_principal] = lambda: Principal("TEST_ONLY_USER")
    return app


def test_authorized_test_stub_is_explicitly_unavailable():
    with TestClient(authorized_app()) as client:
        response = client.post("/api/v1/ai/chat", json=VALID)
        assert response.status_code == 503
        assert response.json()["code"] == "FOUNDATION_ONLY"
        assert "conversation_id" not in response.json()


@pytest.mark.parametrize("payload", [
    {**VALID, "user_id": "victim"},
    {**VALID, "message": "   "},
    {**VALID, "message": "x" * 4001},
    {**VALID, "context": {"screen": "UNKNOWN"}},
    {**VALID, "context": {"screen": "HABIT_DETAIL"}},
    {**VALID, "context": {"screen": "TODAY", "habit_id": "victim"}},
    {**VALID, "context": {"screen": "PROGRESS", "user_id": "victim"}},
])
def test_request_boundary(payload):
    with TestClient(authorized_app()) as client:
        response = client.post("/api/v1/ai/chat", json=payload)
        assert response.status_code == 422
        assert "victim" not in response.text


def test_secret_like_input_is_not_echoed(caplog):
    with TestClient(authorized_app()) as client:
        response = client.post("/api/v1/ai/chat", json={**VALID, "secret": "SECRET_SENTINEL"})
        assert "SECRET_SENTINEL" not in response.text
        assert "SECRET_SENTINEL" not in caplog.text


def test_invalid_config_prevents_startup(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{}")
    from app.config.loader import ConfigurationError
    with pytest.raises(ConfigurationError):
        with TestClient(create_app(path)): pass


def test_canonical_openapi_response():
    schema = create_app().openapi()
    response = schema["components"]["schemas"]["ChatResponse"]["properties"]
    assert "intents" in response and "intent" not in response
    assert "behavior_context" in response
