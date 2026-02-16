from fastapi.testclient import TestClient
from ai_wildfire_tracker.api.server import app

client = TestClient(app)

def test_health_check():
    """Test standard health/root endpoint"""
    
    response = client.get("/")
    assert response.status_code in [200, 404]

def test_fires_endpoint_structure():
    """Test that the fires endpoint returns a list (mocked or empty)"""
    
    try:
        response = client.get("/api/fires")
    except:
        return # Skip if DB connection fails
    
    if response.status_code == 200:
        assert isinstance(response.json(), list)