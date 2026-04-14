from datetime import datetime, timezone
from unittest.mock import patch

import duckdb
import pytest

from ai_wildfire_tracker.ingest.weather import (
    _extract_current_conditions,
    ensure_weather_table,
    get_nws_gridpoint,
    ingest_weather,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mem_db(tmp_path):
    """Create a temp DuckDB database with a seeded fires table."""
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
            (37.77, -122.42, 320.0, 310.0, 15.0, '2026-04-13', '1200', 'h'),
            (34.05, -118.25, 305.0, 298.0,  8.0, '2026-04-13', '0900', 'n')
        """
    )
    con.close()
    return db_file


NWS_POINTS_RESPONSE = {
    "properties": {
        "gridId": "MTR",
        "gridX": 84,
        "gridY": 105,
    }
}

NWS_FORECAST_PROPS = {
    "periods": [
        {
            "windSpeed": "15 mph",
            "temperature": 77,
            "relativeHumidity": {"value": 42},
        }
    ]
}


# ---------------------------------------------------------------------------
# Unit tests: get_nws_gridpoint
# ---------------------------------------------------------------------------


class TestGetNwsGridpoint:
    def test_returns_tuple_on_success(self):
        with patch("ai_wildfire_tracker.ingest.weather._nws_get", return_value=NWS_POINTS_RESPONSE):
            result = get_nws_gridpoint(37.77, -122.42)
        assert result == ("MTR", "84", "105")

    def test_returns_none_on_api_failure(self):
        with patch("ai_wildfire_tracker.ingest.weather._nws_get", return_value=None):
            result = get_nws_gridpoint(37.77, -122.42)
        assert result is None

    def test_returns_none_on_malformed_response(self):
        with patch("ai_wildfire_tracker.ingest.weather._nws_get", return_value={"properties": {}}):
            result = get_nws_gridpoint(37.77, -122.42)
        assert result is None


# ---------------------------------------------------------------------------
# Unit tests: _extract_current_conditions
# ---------------------------------------------------------------------------


class TestExtractCurrentConditions:
    def test_mph_to_kmh_conversion(self):
        props = {
            "periods": [
                {"windSpeed": "10 mph", "temperature": 32, "relativeHumidity": {"value": 50}}
            ]
        }
        result = _extract_current_conditions(props)
        assert result is not None
        assert abs(result["wind_speed_kmh"] - 16.09) < 0.1

    def test_kmh_wind_passthrough(self):
        props = {
            "periods": [
                {"windSpeed": "20 km/h", "temperature": 68, "relativeHumidity": {"value": 30}}
            ]
        }
        result = _extract_current_conditions(props)
        assert result["wind_speed_kmh"] == 20.0

    def test_fahrenheit_to_celsius_conversion(self):
        props = {
            "periods": [{"windSpeed": "0 mph", "temperature": 77, "relativeHumidity": {"value": 0}}]
        }
        result = _extract_current_conditions(props)
        assert result["temp_c"] == 25.0

    def test_humidity_extracted(self):
        props = {
            "periods": [
                {"windSpeed": "5 mph", "temperature": 60, "relativeHumidity": {"value": 65}}
            ]
        }
        result = _extract_current_conditions(props)
        assert result["humidity_pct"] == 65.0

    def test_empty_periods_returns_none(self):
        result = _extract_current_conditions({"periods": []})
        assert result is None

    def test_missing_humidity_defaults_to_zero(self):
        props = {"periods": [{"windSpeed": "5 mph", "temperature": 60}]}
        result = _extract_current_conditions(props)
        assert result["humidity_pct"] == 0.0


# ---------------------------------------------------------------------------
# Integration tests: ingest_weather with temp DB
# ---------------------------------------------------------------------------


class TestIngestWeather:
    def test_inserts_weather_rows(self, mem_db):
        with (
            patch("ai_wildfire_tracker.ingest.weather.DB_PATH", mem_db),
            patch(
                "ai_wildfire_tracker.ingest.weather.get_nws_gridpoint",
                return_value=("MTR", "84", "105"),
            ),
            patch(
                "ai_wildfire_tracker.ingest.weather.get_nws_forecast",
                return_value=NWS_FORECAST_PROPS,
            ),
            patch("ai_wildfire_tracker.ingest.weather.time.sleep"),
        ):
            inserted = ingest_weather(limit=5)

        assert inserted == 2

        con = duckdb.connect(mem_db)
        rows = con.execute("SELECT * FROM weather_observations").fetchall()
        con.close()
        assert len(rows) == 2

    def test_skips_already_fetched_today(self, mem_db):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        con = duckdb.connect(mem_db)
        ensure_weather_table(con)
        con.execute(
            "INSERT INTO weather_observations VALUES (37.77, -122.42, ?, 10.0, 50.0, 20.0, ?)",
            [today, today],
        )
        con.close()

        with (
            patch("ai_wildfire_tracker.ingest.weather.DB_PATH", mem_db),
            patch(
                "ai_wildfire_tracker.ingest.weather.get_nws_gridpoint",
                return_value=("MTR", "84", "105"),
            ),
            patch(
                "ai_wildfire_tracker.ingest.weather.get_nws_forecast",
                return_value=NWS_FORECAST_PROPS,
            ),
            patch("ai_wildfire_tracker.ingest.weather.time.sleep"),
        ):
            inserted = ingest_weather(limit=5)

        # 37.77 already fetched today — only 34.05 is new
        assert inserted == 1

    def test_no_fires_table_returns_zero(self, tmp_path):
        empty_db = str(tmp_path / "empty.db")
        duckdb.connect(empty_db).close()

        with patch("ai_wildfire_tracker.ingest.weather.DB_PATH", empty_db):
            inserted = ingest_weather(limit=5)

        assert inserted == 0

    def test_missing_db_raises(self, tmp_path):
        missing = str(tmp_path / "nonexistent.db")

        with (
            patch("ai_wildfire_tracker.ingest.weather.DB_PATH", missing),
            pytest.raises(FileNotFoundError),
        ):
            ingest_weather()

    def test_offshore_point_skipped(self, mem_db):
        with (
            patch("ai_wildfire_tracker.ingest.weather.DB_PATH", mem_db),
            patch("ai_wildfire_tracker.ingest.weather.get_nws_gridpoint", return_value=None),
            patch("ai_wildfire_tracker.ingest.weather.time.sleep"),
        ):
            inserted = ingest_weather(limit=5)

        assert inserted == 0
