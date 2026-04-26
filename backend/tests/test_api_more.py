import duckdb
import pytest
from fastapi.testclient import TestClient

from ai_wildfire_tracker.api import server

client = TestClient(server.app)


@pytest.fixture(autouse=True)
def setup_teardown_db(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_wildfire_more.db")
    monkeypatch.setattr(server, "DB_PATH", test_db)

    con = duckdb.connect(test_db)
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
        (34.00, -118.00, 350.5, 300.0, 50.0, "2024-01-01", "1200", "high"),
        (36.50, -119.50, 320.0, 280.0, 20.0, "2024-01-02", "1300", "nominal"),
        (31.00, -100.00, 340.0, 290.0, 35.0, "2024-01-03", "1400", "high"),
        (40.00, -120.00, 300.0, 260.0, 10.0, "2024-01-04", "1500", "low"),
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


def test_get_fires_confidence_no_match_returns_empty_list():
    response = client.get("/fires?confidence=veryhigh")
    assert response.status_code == 200
    assert response.json() == []


def test_get_fires_valid_region_with_no_match_returns_empty_list():
    response = client.get("/fires?region=ca&confidence=veryhigh")
    assert response.status_code == 200
    assert response.json() == []


def test_fire_values_have_expected_types():
    response = client.get("/fires")
    assert response.status_code == 200
    data = response.json()

    assert len(data) > 0
    fire = data[0]

    assert isinstance(fire["lat"], (int, float))
    assert isinstance(fire["lon"], (int, float))
    assert isinstance(fire["brightness"], (int, float))
    assert isinstance(fire["frp"], (int, float))
    assert isinstance(fire["confidence"], str)
    assert isinstance(fire["acq_date"], str)
    assert isinstance(fire["acq_time"], str)
    assert isinstance(fire["risk"], (int, float))


def test_fires_are_sorted_newest_first():
    response = client.get("/fires")
    assert response.status_code == 200
    data = response.json()

    dates_times = [(fire["acq_date"], fire["acq_time"]) for fire in data]
    assert dates_times == sorted(dates_times, reverse=True)


def test_health_endpoint_db_exists_true():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert data["database_exists"] is True


def test_health_endpoint_has_expected_types():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data["status"], str)
    assert isinstance(data["database_exists"], bool)
    assert isinstance(data["db_path"], str)
