# backend/tests/test_limit_param.py
"""
Tests for the `limit` query parameter on GET /fires.
"""

import os

import duckdb
import pytest
from fastapi.testclient import TestClient

import ai_wildfire_tracker.api.server as server_module

LIMIT_TEST_DB = "limit_test_wildfire.db"

# Seed more rows than any limit value used in these tests
_SEED_ROWS = [
    (34.0 + i * 0.1, -118.0, 350.0, 300.0, 50.0, f"2024-01-{i+1:02d}", "1200", "high")
    for i in range(10)
]


@pytest.fixture(autouse=True)
def setup_limit_db(monkeypatch):
    if os.path.exists(LIMIT_TEST_DB):
        os.remove(LIMIT_TEST_DB)

    con = duckdb.connect(LIMIT_TEST_DB)
    con.execute(
        """
        CREATE TABLE fires (
            latitude DOUBLE, longitude DOUBLE,
            bright_ti4 DOUBLE, bright_ti5 DOUBLE,
            frp DOUBLE, acq_date VARCHAR, acq_time VARCHAR, confidence VARCHAR
        )
        """
    )
    con.executemany("INSERT INTO fires VALUES (?, ?, ?, ?, ?, ?, ?, ?)", _SEED_ROWS)
    con.close()

    monkeypatch.setattr(server_module, "DB_PATH", LIMIT_TEST_DB)

    yield

    if os.path.exists(LIMIT_TEST_DB):
        os.remove(LIMIT_TEST_DB)


@pytest.fixture()
def client():
    return TestClient(server_module.app)


class TestLimitParameter:
    def test_limit_2_returns_exactly_2_records(self, client):
        """
        GET /fires?limit=2 with 10 records in the DB must return exactly 2.
        Fails when the SQL query ignores the limit param and hardcodes LIMIT 1000.
        """
        response = client.get("/fires?limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2, (
            f"Expected 2 results with limit=2, got {len(response.json())}"
        )

    def test_limit_5_returns_exactly_5_records(self, client):
        """
        GET /fires?limit=5 with 10 records in the DB must return exactly 5.
        """
        response = client.get("/fires?limit=5")
        assert response.status_code == 200
        assert len(response.json()) == 5, (
            f"Expected 5 results with limit=5, got {len(response.json())}"
        )

    def test_limit_default_returns_all_10_records(self, client):
        """
        GET /fires with no limit param must return all 10 seeded records
        (well within the default 1000 cap).
        """
        response = client.get("/fires")
        assert response.status_code == 200
        assert len(response.json()) == 10

    def test_limit_1_returns_single_record(self, client):
        """
        GET /fires?limit=1 must return exactly 1 record — the most recent
        by acq_date DESC, acq_time DESC ordering.
        """
        response = client.get("/fires?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        # Most recent record is the last seeded (highest date index)
        assert data[0]["acq_date"] == "2024-01-10"

    def test_limit_above_row_count_returns_all_rows(self, client):
        """
        GET /fires?limit=500 with only 10 rows must return all 10 —
        limit is a ceiling, not an exact count.
        """
        response = client.get("/fires?limit=500")
        assert response.status_code == 200
        assert len(response.json()) == 10
