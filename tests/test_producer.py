from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_invalid_event_payload():
    payload = {
        "event_type": "page_view"
    }
    response = client.post("/api/v1/events/track", json=payload)
    assert response.status_code == 400