from fastapi.testclient import TestClient
from src.ai_wildfire_tracker.api.server import app

# Create a test client that hooks directly into your FastAPI app
client = TestClient(app)

def test_api_rejects_invalid_region_parameter():
    """
    Test Plan: Edge Case API Validation
    when the data for region is fake/garbage the /fires endpoint will return a 400 Bad Request with a helpful error message.
    """
    # 1. Action: Send request with invalid region 'mars'
    response = client.get("/fires?region=mars")
    
    # 2. Assert: Check that the status code is exactly 400
    assert response.status_code == 400
    
    # 3. Assert: Check that the error message is helpful to the developer
    data = response.json()
    assert "Invalid region 'mars'" in data["detail"]

def test_api_accepts_valid_region_parameter():
    """
    Test Plan: Integration Test
    This helps to make sure that /fires endpoint correctly accepts 'ca' and returns a 200 OK.
    """
    # 1. Action: Send request with valid region 'ca'
    response = client.get("/fires?region=ca")
    
    # 2. Assert: Check that the status code is exactly 200
    assert response.status_code == 200
    
    # 3. Assert: Ensure the payload is a list (even if empty, it should be a valid JSON array)
    assert isinstance(response.json(), list)

def test_health_check_endpoint():
    """
    Test Plan: System Health
    Ensures the server is alive and reporting database status.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"