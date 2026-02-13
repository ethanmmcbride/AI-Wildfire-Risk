from fastapi.testclient import TestClient
from src.ai_wildfire_tracker.api.server import app

client = TestClient(app)

def test_fires_endpoint_status():
    response = client.get("/fires")
    assert response.status_code == 200

def test_fires_returns_list():
    response = client.get("/fires")
    data = response.json()
    assert isinstance(data, list)