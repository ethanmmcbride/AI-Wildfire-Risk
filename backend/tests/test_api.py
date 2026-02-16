# backend/tests/test_api.py
import pytest
import os
import duckdb
from fastapi.testclient import TestClient

# 1. Setup the test environment BEFORE importing the app
TEST_DB = "test_wildfire.db"
os.environ["TEST_DB_PATH"] = TEST_DB

from ai_wildfire_tracker.api.server import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown_db():
    """Fixture to create a temporary DB with sample data before tests."""
    # Setup: Create DB and insert mock data
    con = duckdb.connect(TEST_DB)
    con.execute("""
        CREATE TABLE fires (
            latitude DOUBLE,
            longitude DOUBLE,
            bright_ti4 DOUBLE,
            bright_ti5 DOUBLE,
            frp DOUBLE,
            acq_date VARCHAR,
            acq_time VARCHAR,
            confidence VARCHAR
        )
    """)
    # Insert one sample row
    con.execute("""
        INSERT INTO fires VALUES 
        (34.0, -118.0, 350.5, 300.0, 50.0, '2024-01-01', '1200', 'high')
    """)
    con.close()
    
    yield  # Run the test
    
    # Teardown: Delete the temp DB file
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_get_fires_returns_data():
    """Test that the endpoint correctly reads our mock data."""
    response = client.get("/fires")
    assert response.status_code == 200
    data = response.json()
    
    # Verify we got the list back
    assert isinstance(data, list)
    assert len(data) == 1
    
    # Verify the specific values we inserted
    fire = data[0]
    assert fire["lat"] == 34.0
    assert fire["lon"] == -118.0
    assert fire["confidence"] == "high"

def test_health_check_root():
    """Ensure root doesn't crash."""
    response = client.get("/")
    assert response.status_code in [200, 404]
    