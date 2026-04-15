# backend/tests/integration/test_integration.py
"""
Integration tests for the AI Wildfire Tracker.

Idea is: these tests exercise the real data
pipeline from database write → API read → response parsing. They verify that:

  1. Data written directly via DuckDB is correctly served by the API
  2. Filter logic (region, confidence) operates on real data end-to-end
  3. Database state persists correctly between a write connection and the
     API's read connection (both open the same file)
  4. The risk scoring function produces correct values for known inputs
  5. Ordering guarantees hold across a populated dataset

Integration tests complement unit tests by validating the wiring between
components — bugs that only surface when real connections are involved.
"""

import os

import duckdb
import pytest
from fastapi.testclient import TestClient

import ai_wildfire_tracker.api.server as server_module

INTEG_TEST_DB = "integration_test_wildfire.db"

# Known fire records for deterministic assertions
# (lat, lon, bright_ti4, bright_ti5, frp, acq_date, acq_time, confidence)
KNOWN_FIRES = [
    (34.05, -118.25, 380.0, 320.0, 75.0, "2024-03-15", "1800", "high"),
    (36.77, -119.42, 310.0, 270.0, 18.0, "2024-03-14", "1200", "nominal"),
    (37.88, -122.27, 295.0, 255.0, 8.0, "2024-03-13", "0900", "low"),
    (33.45, -117.10, 425.0, 380.0, 120.0, "2024-03-15", "2000", "high"),
    # Out-of-US-bounds record — must never appear in responses
    (10.0, -70.0, 280.0, 240.0, 5.0, "2024-03-12", "0800", "nominal"),
]


def _create_db_with_fires(db_path: str, rows: list) -> None:
    con = duckdb.connect(db_path)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS fires (
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
    con.executemany("INSERT INTO fires VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
    con.close()


@pytest.fixture(autouse=True)
def integration_db():
    """Create and teardown the integration test database for each test."""
    if os.path.exists(INTEG_TEST_DB):
        os.remove(INTEG_TEST_DB)
    _create_db_with_fires(INTEG_TEST_DB, KNOWN_FIRES)
    yield
    if os.path.exists(INTEG_TEST_DB):
        os.remove(INTEG_TEST_DB)


@pytest.fixture()
def client(monkeypatch):
    """TestClient with DB_PATH patched to the integration test database.
    monkeypatch automatically restores DB_PATH after each test."""
    monkeypatch.setattr(server_module, "DB_PATH", INTEG_TEST_DB)
    return TestClient(server_module.app)


class TestWriteThenReadPipeline:
    def test_records_written_to_db_appear_in_api_response(self, client):
        """
        Data inserted directly via duckdb must be returned by the API.
        Validates that the API and DB share the same file correctly.
        """
        response = client.get("/fires")
        assert response.status_code == 200
        fires = response.json()
        # 4 in-bounds records; 1 out-of-bounds (lat=10.0) excluded by geo-filter
        assert len(fires) == 4

    def test_out_of_bounds_record_excluded_end_to_end(self, client):
        """
        The out-of-bounds record (lat=10, lon=-70) in KNOWN_FIRES must never
        appear in any API response, proving the geo-filter is applied.
        """
        response = client.get("/fires")
        assert response.status_code == 200
        lats = [f["lat"] for f in response.json()]
        assert 10.0 not in lats, "Out-of-bounds fire record leaked through geo-filter"

    def test_data_persists_across_connections(self, client):
        """
        Data written by a separate duckdb connection must be visible to the API.
        Verifies DuckDB file-sharing semantics used in production.
        """
        # Write an additional record via a fresh connection
        extra_con = duckdb.connect(INTEG_TEST_DB)
        extra_con.execute(
            "INSERT INTO fires VALUES "
            "(38.0, -121.0, 300.0, 260.0, 15.0, '2024-03-16', '1000', 'nominal')"
        )
        extra_con.close()

        response = client.get("/fires")
        assert response.status_code == 200
        assert len(response.json()) == 5  # 4 original + 1 new


class TestFilterAccuracyIntegration:
    def test_confidence_high_filter_returns_correct_records(self, client):
        """
        /fires?confidence=high must return exactly the records with confidence='high'.
        End-to-end: DB write → API filter → response validation.
        """
        response = client.get("/fires?confidence=high")
        assert response.status_code == 200
        fires = response.json()
        assert len(fires) == 2, f"Expected 2 high-confidence fires, got {len(fires)}"
        for fire in fires:
            assert fire["confidence"].lower() == "high"

    def test_confidence_low_filter_returns_correct_records(self, client):
        """
        /fires?confidence=low must return exactly the records with confidence='low'.
        """
        response = client.get("/fires?confidence=low")
        assert response.status_code == 200
        fires = response.json()
        assert len(fires) == 1
        assert fires[0]["confidence"].lower() == "low"

    def test_region_ca_filter_excludes_non_california_records(self, client):
        """
        /fires?region=ca must return only fires within California bounding box.
        """
        response = client.get("/fires?region=ca")
        assert response.status_code == 200
        fires = response.json()
        for fire in fires:
            assert 32.5 <= fire["lat"] <= 42.1, f"lat {fire['lat']} outside CA bounds"
            assert -124.5 <= fire["lon"] <= -114.0, f"lon {fire['lon']} outside CA bounds"

    def test_combined_region_and_confidence_filter(self, client):
        """
        /fires?region=ca&confidence=high must return only high-confidence California fires.
        """
        response = client.get("/fires?region=ca&confidence=high")
        assert response.status_code == 200
        fires = response.json()
        for fire in fires:
            assert fire["confidence"].lower() == "high"
            assert 32.5 <= fire["lat"] <= 42.1
            assert -124.5 <= fire["lon"] <= -114.0


class TestRiskScoringIntegration:
    def test_risk_score_is_computed_for_all_records(self, client):
        """
        Every fire in the API response must have a numeric risk score >= 0.
        """
        response = client.get("/fires")
        assert response.status_code == 200
        for fire in response.json():
            assert isinstance(fire["risk"], (int, float))
            assert fire["risk"] >= 0

    def test_risk_score_formula_correctness(self, client):
        """
        risk = round(brightness * 0.6 + frp * 0.4, 2)
        Validates the formula against the known high-confidence record:
          brightness=380.0, frp=75.0 → risk = round(228.0 + 30.0, 2) = 258.0
        """
        response = client.get("/fires?confidence=high")
        assert response.status_code == 200
        fires = response.json()
        # Find the record with brightness=380.0
        target = next((f for f in fires if f["brightness"] == 380.0), None)
        assert target is not None, "Expected fire with brightness=380.0 not found"
        expected_risk = round(380.0 * 0.6 + 75.0 * 0.4, 2)
        assert target["risk"] == expected_risk, (
            f"Risk mismatch: expected {expected_risk}, got {target['risk']}"
        )


class TestOrderingIntegration:
    def test_fires_ordered_by_date_desc_then_time_desc(self, client):
        """
        /fires must return records ordered by acq_date DESC, acq_time DESC.
        Verifies ordering is preserved end-to-end through real DB queries.
        """
        response = client.get("/fires")
        assert response.status_code == 200
        fires = response.json()
        assert len(fires) >= 2

        dates_times = [(f["acq_date"], f["acq_time"]) for f in fires]
        sorted_dates_times = sorted(dates_times, key=lambda x: (x[0], x[1]), reverse=True)
        assert dates_times == sorted_dates_times, (
            f"Fires not ordered correctly.\nGot:      {dates_times}\nExpected: {sorted_dates_times}"
        )
