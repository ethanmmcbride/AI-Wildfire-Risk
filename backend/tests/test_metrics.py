# backend/tests/test_metrics.py
"""
Metrics endpoint tests for the AI Wildfire Tracker API.
"""

import os

import duckdb
import pytest
from fastapi.testclient import TestClient

import ai_wildfire_tracker.api.server as server_module

METRICS_TEST_DB = "metrics_test_wildfire.db"


@pytest.fixture(autouse=True)
def setup_metrics_db(monkeypatch):
    """Seed a minimal DB and patch DB_PATH so metrics tests are isolated."""
    if os.path.exists(METRICS_TEST_DB):
        os.remove(METRICS_TEST_DB)

    con = duckdb.connect(METRICS_TEST_DB)
    con.execute(
        """
        CREATE TABLE fires (
            latitude DOUBLE, longitude DOUBLE,
            bright_ti4 DOUBLE, bright_ti5 DOUBLE,
            frp DOUBLE, acq_date VARCHAR, acq_time VARCHAR, confidence VARCHAR
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

    monkeypatch.setattr(server_module, "DB_PATH", METRICS_TEST_DB)

    yield

    if os.path.exists(METRICS_TEST_DB):
        os.remove(METRICS_TEST_DB)


@pytest.fixture()
def client():
    return TestClient(server_module.app)


class TestMetricsEndpoint:
    def test_metrics_endpoint_returns_200(self, client):
        """
        GET /metrics must return HTTP 200.
        """
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_has_required_fields(self, client):
        """
        /metrics must expose uptime_seconds, request_counts, and
        last_fires_response_ms so operations can observe the live deployment.
        """
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data, "Missing uptime_seconds"
        assert "request_counts" in data, "Missing request_counts"
        assert "last_fires_response_ms" in data, "Missing last_fires_response_ms"

    def test_request_counts_tracks_fires_and_health(self, client):
        """
        request_counts must include per-endpoint counters for fires and health
        so the operations dashboard can show per-route traffic.
        """
        data = client.get("/metrics").json()
        counts = data["request_counts"]
        assert "fires" in counts, "fires counter missing from request_counts"
        assert "health" in counts, "health counter missing from request_counts"

    def test_fires_counter_increments_after_fires_request(self, client):
        """
        After calling /fires, the fires counter in /metrics must increase by 1.
        Validates that request instrumentation is correctly wired to the handler.
        """
        before = client.get("/metrics").json()["request_counts"]["fires"]
        client.get("/fires")
        after = client.get("/metrics").json()["request_counts"]["fires"]
        assert after == before + 1, (
            f"fires counter did not increment: before={before}, after={after}"
        )

    def test_last_fires_response_ms_populated_after_fires_call(self, client):
        """
        After at least one /fires call, last_fires_response_ms must be a
        non-negative float, proving wall-clock response tracking is active.
        """
        client.get("/fires")
        data = client.get("/metrics").json()
        assert data["last_fires_response_ms"] is not None
        assert isinstance(data["last_fires_response_ms"], float)
        assert data["last_fires_response_ms"] >= 0.0

    def test_uptime_seconds_is_non_negative_float(self, client):
        """
        uptime_seconds must be >= 0.0, confirming the process-start timestamp
        is correctly captured at module import time.
        """
        data = client.get("/metrics").json()
        assert isinstance(data["uptime_seconds"], float)
        assert data["uptime_seconds"] >= 0.0
