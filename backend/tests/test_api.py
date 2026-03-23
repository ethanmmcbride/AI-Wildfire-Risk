# backend/tests/test_api.py
import os

import duckdb
import pytest
from fastapi.testclient import TestClient

TEST_DB = "test_wildfire.db"
os.environ["TEST_DB_PATH"] = TEST_DB

from ai_wildfire_tracker.api.server import app  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_teardown_db():
    """Create a temporary DB with sample data before each test."""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    con = duckdb.connect(TEST_DB)
    con.execute(
        """
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
        """
    )

    rows = [
        (34.0, -118.0, 350.5, 300.0, 50.0, "2024-01-01", "1200", "high"),
        (36.5, -119.5, 320.0, 280.0, 20.0, "2024-01-02", "1300", "nominal"),
        (31.0, -100.0, 340.0, 290.0, 35.0, "2024-01-03", "1400", "high"),
        (10.0, -70.0, 280.0, 250.0, 5.0, "2024-01-01", "1300", "low"),
    ]

    con.executemany(
        """
        INSERT INTO fires (
            latitude, longitude, bright_ti4, bright_ti5,
            frp, acq_date, acq_time, confidence
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    con.close()

    yield

    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "database_exists" in data
    assert "db_path" in data


def test_get_fires_returns_us_data_only():
    response = client.get("/fires")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 3

    for fire in data:
        assert 24.0 <= fire["lat"] <= 49.5
        assert -125.0 <= fire["lon"] <= -66.5


def test_get_fires_confidence_high():
    response = client.get("/fires?confidence=high")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    for fire in data:
        assert fire["confidence"].lower() == "high"


def test_get_fires_region_ca():
    response = client.get("/fires?region=ca")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    for fire in data:
        assert 32.5 <= fire["lat"] <= 42.1
        assert -124.5 <= fire["lon"] <= -114.0


def test_get_fires_region_ca_and_confidence_high():
    response = client.get("/fires?region=ca&confidence=high")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["confidence"].lower() == "high"


def test_invalid_region_returns_400():
    response = client.get("/fires?region=invalid")
    assert response.status_code == 400
    data = response.json()
    assert "Invalid region" in data["detail"]


def test_fire_has_expected_fields():
    response = client.get("/fires")
    assert response.status_code == 200
    fire = response.json()[0]

    expected_fields = {
        "lat",
        "lon",
        "brightness",
        "frp",
        "confidence",
        "risk",
        "acq_date",
        "acq_time",
    }
    assert expected_fields.issubset(fire.keys())


def test_risk_score_is_numeric():
    response = client.get("/fires")
    assert response.status_code == 200
    data = response.json()

    for fire in data:
        assert isinstance(fire["risk"], (int, float))
        assert fire["risk"] >= 0
