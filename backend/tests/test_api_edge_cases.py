# Resubmission for Sprint 2 = Tomphaeton Phu: added Lines 58 - 104 and 188 - 237
import importlib
import os

import duckdb
import pytest
from fastapi.testclient import TestClient

TEST_DB = "test_wildfire_edge.db"


@pytest.fixture(autouse=True)
def cleanup_db():
    os.environ["TEST_DB_PATH"] = TEST_DB

    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    yield

    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    os.environ.pop("TEST_DB_PATH", None)


@pytest.fixture()
def client():
    import ai_wildfire_tracker.api.server as server_module

    server_module = importlib.reload(server_module)
    return TestClient(server_module.app)


@pytest.fixture()
def compute_risk():
    import ai_wildfire_tracker.api.server as server_module

    server_module = importlib.reload(server_module)
    return server_module.compute_risk


def test_get_fires_returns_empty_list_when_db_missing(client):
    response = client.get("/fires")
    assert response.status_code == 200
    assert response.json() == []


def test_get_fires_returns_empty_list_when_table_missing(client):
    con = duckdb.connect(TEST_DB)
    con.close()

    response = client.get("/fires")
    assert response.status_code == 200
    assert response.json() == []


def test_api_rejects_invalid_region_parameter(client):
    response = client.get("/fires?region=mars")
    assert response.status_code == 400

    data = response.json()
    assert "Invalid region" in data["detail"]


def test_api_accepts_valid_region_parameter(client):
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

    response = client.get("/fires?region=ca")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_region_us_returns_only_us_records(client):
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

    response = client.get("/fires?region=us")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 3
    for fire in data:
        assert 24.0 <= fire["lat"] <= 49.5
        assert -125.0 <= fire["lon"] <= -66.5


def test_confidence_filter_with_no_matches_returns_empty_list(client):
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

    response = client.get("/fires?confidence=low")
    assert response.status_code == 200
    assert response.json() == []


def test_api_sqli_defense(client):
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

    malicious_payload = "high' OR '1'='1"
    response = client.get(f"/fires?confidence={malicious_payload}")

    assert response.status_code == 200
    assert response.json() == []


def test_health_check_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_compute_risk_logic_boundaries(compute_risk):
    assert compute_risk(350.0, 50.0) == 230.0
    assert compute_risk(0.0, 0.0) == 0.0
    assert compute_risk(None, None) == 0.0
    assert compute_risk(350.0, None) == 210.0