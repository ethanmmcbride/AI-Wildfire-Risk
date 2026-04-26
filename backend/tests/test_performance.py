import time

import duckdb
import pytest
from fastapi.testclient import TestClient

from ai_wildfire_tracker.api import server

client = TestClient(server.app)


@pytest.fixture(autouse=True)
def setup_large_db(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_performance.db")
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

    rows = []
    for i in range(1000):
        lat = 32.5 + (i % 50) * 0.1
        lon = -124.0 + (i % 50) * 0.1
        bright_ti4 = 300.0 + (i % 100)
        bright_ti5 = 280.0 + (i % 50)
        frp = 10.0 + (i % 40)
        acq_date = "2025-06-01"
        acq_time = f"{800 + (i % 200):04d}"
        confidence = ["low", "nominal", "high"][i % 3]
        rows.append((lat, lon, bright_ti4, bright_ti5, frp, acq_date, acq_time, confidence))

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


def test_fires_endpoint_returns_within_one_second():
    start = time.perf_counter()
    response = client.get("/fires")
    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert elapsed < 1.0


def test_fires_endpoint_region_filter_returns_within_one_second():
    start = time.perf_counter()
    response = client.get("/fires?region=ca")
    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert elapsed < 1.0


def test_fires_endpoint_confidence_filter_returns_within_one_second():
    start = time.perf_counter()
    response = client.get("/fires?confidence=high")
    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert elapsed < 1.0
