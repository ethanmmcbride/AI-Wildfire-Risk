from fastapi.testclient import TestClient
from src.ai_wildfire_tracker.api.server import app
from src.ai_wildfire_tracker.api.server import compute_risk

client = TestClient(app)

def test_api_rejects_invalid_region_parameter():
    """
    Test Plan: Edge Case API Validation
    when the data for region is fake/garbage the /fires endpoint will return a 400 Bad Request with a helpful error message.
    """
    # 1. Send request with invalid region 'mars'
    response = client.get("/fires?region=mars")
    
    # 2. Check that the status code is exactly 400
    assert response.status_code == 400
    
    # 3. Check that the error message is helpful to the developer
    data = response.json()
    assert "Invalid region 'mars'" in data["detail"]

def test_api_accepts_valid_region_parameter():
    """
    Test Plan: Integration Test
    This helps to make sure that /fires endpoint correctly accepts 'ca' and returns a 200 OK.
    """
    # 1. Send request with valid region 'ca'
    response = client.get("/fires?region=ca")
    
    # 2. Check that the status code is exactly 200
    assert response.status_code == 200
    
    # 3. Ensure the payload is a list (even if empty, it should be a valid JSON array)
    assert isinstance(response.json(), list)

def test_health_check_endpoint():
    """
    Test Plan: System Health
    Making sure that the server is alive and reporting database status
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_sqli_defense():
    """
    Test Plan: Security 
    Making sure that SQL payloads in the parameter will not manipulate the db query and will be treated 
    regular strings
    """
    # 1. Send a classic SQL injection payload
    malicious_payload = "high' OR '1'='1"
    response = client.get(f"/fires?confidence={malicious_payload}")

    # 2. The server should not crash (500) and should return a normal 200 OK.
    assert response.status_code == 200

    # 3. Because the payload is safely escaped as a literal string, it won't match any real confidence levels, returning an empty list.
    assert response.json() == []

def test_compute_risk_logic_boundaries():
    """
    Test Plan: Unit Testing (Boundary Value Analysis)
    making sure the math calculation handles none types and zeroes safely.
    """
    # Test 1: Standard values (0.6 * 350) + (0.4 * 50) = 210 + 20 = 230.0
    assert compute_risk(350.0, 50.0) == 230.0

    # Test 2: Absolute zeroes
    assert compute_risk(0.0, 0.0) == 0.0

    # Test 3: Handling missing database data (None types)
    assert compute_risk(None, None) == 0.0
    assert compute_risk(350.0, None) == 210.0