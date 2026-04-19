"""
test_ndvi.py — pytest tests for the Open-Meteo environmental conditions ingestor
backend/tests/test_ndvi.py

Test methodology: unit tests with mocked HTTP calls and a self-contained
DuckDB fixture. No live Open-Meteo API calls are made.

Coverage (TC-07 to TC-14):
    TC-07  fetch_environmental_conditions: success path, all three values returned
    TC-08  fetch_environmental_conditions: API failure returns None gracefully
    TC-09  fetch_environmental_conditions: null values default to 0.0
    TC-10  ingest_environmental: happy path inserts rows for all fire points
    TC-11  ingest_environmental: dedup skips already-fetched points
    TC-12  ingest_environmental: missing fires table returns 0
    TC-13  ingest_environmental: missing DB raises FileNotFoundError
    TC-14  ingest_environmental: API failure for all points returns 0
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import duckdb
import pytest

from ai_wildfire_tracker.ingest.ndvi import (
    _already_fetched_today,
    ensure_environmental_table,
    fetch_environmental_conditions,
    ingest_environmental,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mem_db(tmp_path):
    """Temp DuckDB with seeded fires table — two US fire detection points."""
    db_file = str(tmp_path / "test_wildfire.db")
    con = duckdb.connect(db_file)
    con.execute(
        """
        CREATE TABLE fires (
            latitude DOUBLE, longitude DOUBLE,
            bright_ti4 DOUBLE, bright_ti5 DOUBLE,
            frp DOUBLE, acq_date VARCHAR, acq_time VARCHAR, confidence VARCHAR
        )
        """
    )
    con.execute(
        """
        INSERT INTO fires VALUES
            (37.77, -122.42, 320.0, 310.0, 15.0, '2026-04-18', '1200', 'h'),
            (34.05, -118.25, 305.0, 298.0,  8.0, '2026-04-18', '0900', 'n')
        """
    )
    con.close()
    return db_file


# ---------------------------------------------------------------------------
# Shared mock API response — matches real Open-Meteo structure (verified Postman)
# ---------------------------------------------------------------------------

OPEN_METEO_RESPONSE = {
    "hourly": {
        "time": ["2026-04-18T00:00", "2026-04-18T01:00"],
        "soil_moisture_0_to_1cm": [0.12, 0.14],
    },
    "daily": {
        "time": ["2026-04-18"],
        "vapor_pressure_deficit_max": [1.95],
        "et0_fao_evapotranspiration": [4.48],
    },
}


def _make_mock_response(data: dict) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = data
    return mock


# ---------------------------------------------------------------------------
# Unit tests: fetch_environmental_conditions (TC-07 to TC-09)
# ---------------------------------------------------------------------------


class TestFetchEnvironmentalConditions:
    def test_tc07_returns_correct_values_on_success(self):
        """TC-07: All three values returned and correctly parsed."""
        with patch(
            "ai_wildfire_tracker.ingest.ndvi.SESSION.get",
            return_value=_make_mock_response(OPEN_METEO_RESPONSE),
        ):
            result = fetch_environmental_conditions(37.77, -122.42)

        assert result is not None
        # soil_moisture = mean([0.12, 0.14]) = 0.13
        assert abs(result["soil_moisture"] - 0.13) < 0.001
        assert abs(result["vpd_kpa"] - 1.95) < 0.001
        assert abs(result["et0_mm"] - 4.48) < 0.001

    def test_tc08_returns_none_on_request_failure(self):
        """TC-08: Network error returns None, no crash."""
        import requests

        with patch(
            "ai_wildfire_tracker.ingest.ndvi.SESSION.get",
            side_effect=requests.RequestException("timeout"),
        ):
            result = fetch_environmental_conditions(37.77, -122.42)

        assert result is None

    def test_tc09_null_values_default_to_zero(self):
        """TC-09: None values in response default to 0.0."""
        response = {
            "hourly": {
                "time": ["2026-04-18T00:00"],
                "soil_moisture_0_to_1cm": [None],
            },
            "daily": {
                "time": ["2026-04-18"],
                "vapor_pressure_deficit_max": [None],
                "et0_fao_evapotranspiration": [None],
            },
        }
        with patch(
            "ai_wildfire_tracker.ingest.ndvi.SESSION.get",
            return_value=_make_mock_response(response),
        ):
            result = fetch_environmental_conditions(37.77, -122.42)

        assert result is not None
        assert result["soil_moisture"] == 0.0
        assert result["vpd_kpa"] == 0.0
        assert result["et0_mm"] == 0.0

    def test_returns_none_on_missing_keys(self):
        """Malformed response missing expected keys returns None."""
        with patch(
            "ai_wildfire_tracker.ingest.ndvi.SESSION.get",
            return_value=_make_mock_response({"unexpected": {}}),
        ):
            result = fetch_environmental_conditions(37.77, -122.42)

        assert result is None

    def test_soil_moisture_is_mean_of_hourly_values(self):
        """Soil moisture is averaged across all hourly values."""
        response = {
            "hourly": {
                "time": ["2026-04-18T00:00", "2026-04-18T01:00", "2026-04-18T02:00"],
                "soil_moisture_0_to_1cm": [0.10, 0.20, 0.30],
            },
            "daily": {
                "time": ["2026-04-18"],
                "vapor_pressure_deficit_max": [1.0],
                "et0_fao_evapotranspiration": [2.0],
            },
        }
        with patch(
            "ai_wildfire_tracker.ingest.ndvi.SESSION.get",
            return_value=_make_mock_response(response),
        ):
            result = fetch_environmental_conditions(37.77, -122.42)

        assert result is not None
        assert abs(result["soil_moisture"] - 0.20) < 0.001


# ---------------------------------------------------------------------------
# Unit tests: dedup helper
# ---------------------------------------------------------------------------


class TestAlreadyFetchedToday:
    def test_returns_false_when_table_empty(self, mem_db):
        con = duckdb.connect(mem_db)
        ensure_environmental_table(con)
        result = _already_fetched_today(con, 37.77, -122.42, "2026-04-18")
        con.close()
        assert result is False

    def test_returns_true_when_row_exists(self, mem_db):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        con = duckdb.connect(mem_db)
        ensure_environmental_table(con)
        con.execute(
            "INSERT INTO environmental_conditions VALUES (37.77, -122.42, ?, 0.1, 1.5, 3.0, ?)",
            [today, today],
        )
        result = _already_fetched_today(con, 37.77, -122.42, today)
        con.close()
        assert result is True


# ---------------------------------------------------------------------------
# Integration tests: ingest_environmental (TC-10 to TC-14)
# ---------------------------------------------------------------------------


class TestIngestEnvironmental:
    def test_tc10_inserts_rows_for_all_fire_points(self, mem_db):
        """TC-10: Happy path — 2 fire points in DB → 2 rows inserted."""
        with (
            patch("ai_wildfire_tracker.ingest.ndvi.DB_PATH", mem_db),
            patch(
                "ai_wildfire_tracker.ingest.ndvi.SESSION.get",
                return_value=_make_mock_response(OPEN_METEO_RESPONSE),
            ),
            patch("ai_wildfire_tracker.ingest.ndvi.time.sleep"),
        ):
            inserted = ingest_environmental(limit=10)

        assert inserted == 2

        con = duckdb.connect(mem_db)
        rows = con.execute("SELECT * FROM environmental_conditions").fetchall()
        con.close()
        assert len(rows) == 2

    def test_tc11_skips_already_fetched_point(self, mem_db):
        """TC-11: Point already fetched today is skipped, only new point inserted."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        con = duckdb.connect(mem_db)
        ensure_environmental_table(con)
        con.execute(
            "INSERT INTO environmental_conditions VALUES (37.77, -122.42, ?, 0.1, 1.5, 3.0, ?)",
            [today, today],
        )
        con.close()

        with (
            patch("ai_wildfire_tracker.ingest.ndvi.DB_PATH", mem_db),
            patch(
                "ai_wildfire_tracker.ingest.ndvi.SESSION.get",
                return_value=_make_mock_response(OPEN_METEO_RESPONSE),
            ),
            patch("ai_wildfire_tracker.ingest.ndvi.time.sleep"),
        ):
            inserted = ingest_environmental(limit=10)

        assert inserted == 1

    def test_tc12_no_fires_table_returns_zero(self, tmp_path):
        """TC-12: No fires table in DB returns 0 without crashing."""
        empty_db = str(tmp_path / "empty.db")
        duckdb.connect(empty_db).close()

        with patch("ai_wildfire_tracker.ingest.ndvi.DB_PATH", empty_db):
            inserted = ingest_environmental(limit=10)

        assert inserted == 0

    def test_tc13_missing_db_raises(self, tmp_path):
        """TC-13: Missing DB file raises FileNotFoundError."""
        missing = str(tmp_path / "nonexistent.db")

        with (
            patch("ai_wildfire_tracker.ingest.ndvi.DB_PATH", missing),
            pytest.raises(FileNotFoundError),
        ):
            ingest_environmental()

    def test_tc14_api_failure_skips_all_points(self, mem_db):
        """TC-14: API failure for every point results in 0 rows inserted."""
        import requests

        with (
            patch("ai_wildfire_tracker.ingest.ndvi.DB_PATH", mem_db),
            patch(
                "ai_wildfire_tracker.ingest.ndvi.SESSION.get",
                side_effect=requests.RequestException("timeout"),
            ),
            patch("ai_wildfire_tracker.ingest.ndvi.time.sleep"),
        ):
            inserted = ingest_environmental(limit=10)

        assert inserted == 0
