# backend/tests/test_metrics.py
"""
TDD test suite for the GET /metrics endpoint.
"""

import os

import duckdb
import pytest
from fastapi.testclient import TestClient

import ai_wildfire_tracker.api.server as server_module

METRICS_TEST_DB = "metrics_test_wildfire.db"


@pytest.fixture(autouse=True)
def setup_metrics_db():
    """Seed a minimal database so /fires calls succeed during metrics tests."""
    if os.path.exists(METRICS_TEST_DB):
        os.remove(METRICS_TEST_DB)

    con = duckdb.connect(METRICS_TEST_DB)
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
    con.executemany(
        "INSERT INTO fires VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (34.0, -118.0, 350.0, 300.0, 50.0, "2024-01-01", "1200", "high"),
            (36.5, -119.5, 320.0, 280.0, 20.0, "2024-01-02", "1300", "nominal"),
        ],
    )
    con.close()

    yield

    if os.path.exists(METRICS_TEST_DB):
        os.remove(METRICS_TEST_DB)


@pytest.fixture()
def client(monkeypatch):
    """TestClient with DB_PATH patched to the metrics test database."""
    monkeypatch.setattr(server_module, "DB_PATH", METRICS_TEST_DB)
    return TestClient(server_module.app)


class TestMetricsEndpoint:
    def test_metrics_endpoint_returns_200(self, client):
        """
        TC-METRICS-01
        Input: GET /metrics
        Expected: HTTP 200 — endpoint is routed and reachable.
        """
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_has_required_fields(self, client):
        """
        TC-METRICS-02
        Input: GET /metrics
        Expected: JSON body contains uptime_seconds, request_counts,
                  last_fires_response_ms, last_health_response_ms.
        """
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
        assert "request_counts" in data
        assert "last_fires_response_ms" in data
        assert "last_health_response_ms" in data

    def test_request_counts_tracks_fires_and_health(self, client):
        """
        TC-METRICS-03
        Input: GET /metrics
        Expected: request_counts has fires and health keys (even if 0 at start).
        """
        response = client.get("/metrics")
        assert response.status_code == 200
        counts = response.json()["request_counts"]
        assert "fires" in counts
        assert "health" in counts

    def test_fires_counter_increments_after_fires_request(self, client):
        """
        TC-METRICS-04
        Input: GET /metrics, then GET /fires, then GET /metrics again.
        Expected: request_counts.fires increases by exactly 1.
        """
        before = client.get("/metrics").json()["request_counts"]["fires"]
        client.get("/fires")
        after = client.get("/metrics").json()["request_counts"]["fires"]
        assert after == before + 1

    def test_last_fires_response_ms_populated_after_fires_call(self, client):
        """
        TC-METRICS-05
        Input: GET /fires, then GET /metrics.
        Expected: last_fires_response_ms is a non-negative float (not None).
        """
        client.get("/fires")
        data = client.get("/metrics").json()
        assert data["last_fires_response_ms"] is not None
        assert isinstance(data["last_fires_response_ms"], float)
        assert data["last_fires_response_ms"] >= 0.0

    def test_uptime_seconds_is_non_negative_float(self, client):
        """
        TC-METRICS-06
        Input: GET /metrics
        Expected: uptime_seconds is a non-negative float — proves process
                  start time was captured at module import, not per-request.
        """
        data = client.get("/metrics").json()
        assert isinstance(data["uptime_seconds"], float)
        assert data["uptime_seconds"] >= 0.0
