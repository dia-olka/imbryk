"""Ingestion API unit tests."""

from fastapi.testclient import TestClient

from ingestion_api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_submit_prompt():
    response = client.post(
        "/prompts",
        json={"prompt": "test prompt", "user_id": "user-1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
