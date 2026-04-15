# backend/tests/performance/test_performance.py
"""
Performance tests for the AI Wildfire Tracker API.

This is for Response-Time SLA Testing
These tests will be checking API endpoints to see if it meets defined Service Level Agreement (SLA).
Each test measures wall-clock response
time using stdlib `time.perf_counter` to avoid external dependencies.

SLAs defined:
  - /fires       : < 500ms
  - /health      : < 100ms
  - /fires?...   : < 500ms with any valid filter combination

These tests complement unit tests by catching regressions in database query
performance, serialization overhead, and middleware latency.
"""

import os
import time

import duckdb
import pytest
from fastapi.testclient import TestClient

import ai_wildfire_tracker.api.server as server_module

PERF_TEST_DB = "perf_test_wildfire.db"

# SLA thresholds in seconds
SLA_FIRES_S = 0.500
SLA_HEALTH_S = 0.100
SAMPLE_SIZE = 5  # number of consecutive requests for each SLA check


@pytest.fixture(autouse=True)
def setup_perf_db():
    """Seed a deterministic database with 50 fire records for performance tests."""
    if os.path.exists(PERF_TEST_DB):
        os.remove(PERF_TEST_DB)

    con = duckdb.connect(PERF_TEST_DB)
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
    confidences = ["high", "nominal", "low"]
    for i in range(50):
        lat = 32.5 + (i % 10) * 0.5
        lon = -120.0 + (i % 8) * 0.5
        rows.append(
            (
                lat,
                lon,
                320.0 + i,
                280.0 + i,
                10.0 + i,
                "2024-01-15",
                f"{1000 + i * 10:04d}",
                confidences[i % 3],
            )
        )

    con.executemany("INSERT INTO fires VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
    con.close()

    yield

    if os.path.exists(PERF_TEST_DB):
        os.remove(PERF_TEST_DB)


@pytest.fixture()
def client(monkeypatch):
    """TestClient with DB_PATH patched to the performance test database.
    monkeypatch automatically restores DB_PATH after each test."""
    monkeypatch.setattr(server_module, "DB_PATH", PERF_TEST_DB)
    return TestClient(server_module.app)


def measure_response_time(client: TestClient, url: str) -> float:
    """Return wall-clock response time in seconds for a single GET request."""
    start = time.perf_counter()
    response = client.get(url)
    elapsed = time.perf_counter() - start
    assert response.status_code == 200, f"Unexpected status {response.status_code} for {url}"
    return elapsed


class TestFiresEndpointSLA:
    def test_fires_endpoint_responds_under_500ms(self, client):
        """The /fires endpoint must respond within 500ms (SLA)."""
        elapsed = measure_response_time(client, "/fires")
        assert elapsed < SLA_FIRES_S, (
            f"/fires responded in {elapsed * 1000:.1f}ms, exceeds SLA of {SLA_FIRES_S * 1000}ms"
        )

    def test_fires_region_filter_responds_under_500ms(self, client):
        """Filtered /fires?region=ca must respond within 500ms."""
        elapsed = measure_response_time(client, "/fires?region=ca")
        assert elapsed < SLA_FIRES_S, (
            f"/fires?region=ca responded in {elapsed * 1000:.1f}ms, "
            f"exceeds SLA of {SLA_FIRES_S * 1000}ms"
        )

    def test_fires_confidence_filter_responds_under_500ms(self, client):
        """Filtered /fires?confidence=high must respond within 500ms."""
        elapsed = measure_response_time(client, "/fires?confidence=high")
        assert elapsed < SLA_FIRES_S, (
            f"/fires?confidence=high responded in {elapsed * 1000:.1f}ms, "
            f"exceeds SLA of {SLA_FIRES_S * 1000}ms"
        )

    def test_fires_combined_filter_responds_under_500ms(self, client):
        """Combined filter /fires?region=ca&confidence=high must respond within 500ms."""
        elapsed = measure_response_time(client, "/fires?region=ca&confidence=high")
        assert elapsed < SLA_FIRES_S, (
            f"/fires?region=ca&confidence=high responded in {elapsed * 1000:.1f}ms, "
            f"exceeds SLA of {SLA_FIRES_S * 1000}ms"
        )

    def test_fires_endpoint_consistent_across_repeated_calls(self, client):
        """Five consecutive /fires requests must each stay under SLA (no degradation)."""
        times = []
        for _ in range(SAMPLE_SIZE):
            times.append(measure_response_time(client, "/fires"))

        violations = [t for t in times if t >= SLA_FIRES_S]
        assert not violations, (
            f"{len(violations)}/{SAMPLE_SIZE} requests exceeded {SLA_FIRES_S * 1000}ms SLA. "
            f"Times (ms): {[f'{t * 1000:.1f}' for t in times]}"
        )


class TestHealthEndpointSLA:
    def test_health_endpoint_responds_under_100ms(self, client):
        """The /health endpoint must respond within 100ms (SLA)."""
        elapsed = measure_response_time(client, "/health")
        assert elapsed < SLA_HEALTH_S, (
            f"/health responded in {elapsed * 1000:.1f}ms, exceeds SLA of {SLA_HEALTH_S * 1000}ms"
        )

    def test_health_endpoint_consistent_across_repeated_calls(self, client):
        """Five consecutive /health requests must each stay under SLA."""
        times = []
        for _ in range(SAMPLE_SIZE):
            times.append(measure_response_time(client, "/health"))

        violations = [t for t in times if t >= SLA_HEALTH_S]
        assert not violations, (
            f"{len(violations)}/{SAMPLE_SIZE} /health requests exceeded "
            f"{SLA_HEALTH_S * 1000}ms SLA. "
            f"Times (ms): {[f'{t * 1000:.1f}' for t in times]}"
        )
