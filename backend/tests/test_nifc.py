"""
test_nifc.py — pytest tests for the NIFC fire perimeter ingestor
backend/tests/test_nifc.py

Test methodology: unit tests with mocked HTTP calls and a self-contained
DuckDB fixture. No live NIFC API calls are made. Shapely used for spatial ops.

Coverage (TC-15 to TC-23):
    TC-15  fetch_nifc_perimeters: success path returns feature list
    TC-16  fetch_nifc_perimeters: API failure returns empty list
    TC-17  point_in_any_perimeter: point inside polygon → True
    TC-18  point_in_any_perimeter: point outside all polygons → False
    TC-19  label_fire_detections: point inside perimeter gets label 1
    TC-20  label_fire_detections: point outside perimeter gets label 0
    TC-21  label_fire_detections: already-labeled points are skipped
    TC-22  ingest_nifc: happy path returns correct summary dict
    TC-23  ingest_nifc: missing DB raises FileNotFoundError
"""

from unittest.mock import MagicMock, patch

import duckdb
import pytest

from ai_wildfire_tracker.ingest.nifc import (
    build_shapely_polygons,
    ensure_labels_table,
    ensure_perimeter_table,
    fetch_nifc_perimeters,
    ingest_nifc,
    label_fire_detections,
    point_in_any_perimeter,
    store_perimeters,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mem_db(tmp_path):
    """Temp DuckDB with seeded fires — SF point (inside test polygon) and LA point (outside)."""
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
            (37.77, -122.42, 320.0, 310.0, 15.0, '2026-04-19', '1200', 'h'),
            (34.05, -118.25, 305.0, 298.0,  8.0, '2026-04-19', '0900', 'n')
        """
    )
    con.close()
    return db_file


# ---------------------------------------------------------------------------
# GeoJSON test fixture — small square covering SF area only
# ---------------------------------------------------------------------------

SF_POLYGON_FEATURE = {
    "type": "Feature",
    "properties": {
        "poly_IncidentName": "TEST FIRE",
        "poly_GISAcres": 500.0,
        "poly_CreateDate": "2026-04-19",
    },
    "geometry": {
        "type": "Polygon",
        "coordinates": [
            [
                [-123.0, 37.5],
                [-122.0, 37.5],
                [-122.0, 38.0],
                [-123.0, 38.0],
                [-123.0, 37.5],
            ]
        ],
    },
}


def _make_mock_response(data: dict) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = data
    return mock


# ---------------------------------------------------------------------------
# Unit tests: fetch_nifc_perimeters (TC-15, TC-16)
# ---------------------------------------------------------------------------


class TestFetchNifcPerimeters:
    def test_tc15_returns_feature_list_on_success(self):
        """TC-15: Successful API call returns list of GeoJSON features."""
        with patch(
            "ai_wildfire_tracker.ingest.nifc.SESSION.get",
            return_value=_make_mock_response({"features": [SF_POLYGON_FEATURE]}),
        ):
            result = fetch_nifc_perimeters()

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["properties"]["poly_IncidentName"] == "TEST FIRE"

    def test_tc16_returns_empty_list_on_api_failure(self):
        """TC-16: Network error returns empty list, no crash."""
        import requests

        with patch(
            "ai_wildfire_tracker.ingest.nifc.SESSION.get",
            side_effect=requests.RequestException("timeout"),
        ):
            result = fetch_nifc_perimeters()

        assert result == []

    def test_returns_empty_list_on_api_error_response(self):
        """ArcGIS error JSON response returns empty list."""
        with patch(
            "ai_wildfire_tracker.ingest.nifc.SESSION.get",
            return_value=_make_mock_response(
                {"error": {"code": 400, "message": "bad request"}}
            ),
        ):
            result = fetch_nifc_perimeters()

        assert result == []

    def test_returns_empty_list_on_missing_features_key(self):
        """Malformed response missing 'features' key returns empty list."""
        with patch(
            "ai_wildfire_tracker.ingest.nifc.SESSION.get",
            return_value=_make_mock_response({}),
        ):
            result = fetch_nifc_perimeters()

        assert result == []


# ---------------------------------------------------------------------------
# Unit tests: spatial helpers (TC-17, TC-18)
# ---------------------------------------------------------------------------


class TestSpatialHelpers:
    def setup_method(self):
        self.polygons = build_shapely_polygons([SF_POLYGON_FEATURE])

    def test_tc17_point_inside_polygon_returns_true(self):
        """TC-17: SF point (37.77, -122.42) inside test polygon → True."""
        assert point_in_any_perimeter(37.77, -122.42, self.polygons) is True

    def test_tc18_point_outside_all_polygons_returns_false(self):
        """TC-18: LA point (34.05, -118.25) outside test polygon → False."""
        assert point_in_any_perimeter(34.05, -118.25, self.polygons) is False

    def test_empty_polygon_list_always_returns_false(self):
        """No polygons loaded → always returns False."""
        assert point_in_any_perimeter(37.77, -122.42, []) is False

    def test_build_shapely_polygons_returns_valid_geometries(self):
        """Valid GeoJSON feature produces exactly one Shapely polygon."""
        polygons = build_shapely_polygons([SF_POLYGON_FEATURE])
        assert len(polygons) == 1
        assert polygons[0].is_valid


# ---------------------------------------------------------------------------
# Integration tests: label_fire_detections (TC-19, TC-20, TC-21)
# ---------------------------------------------------------------------------


class TestLabelFireDetections:
    def test_tc19_point_inside_perimeter_gets_label_1(self, mem_db):
        """TC-19: SF detection inside polygon → label = 1."""
        polygons = build_shapely_polygons([SF_POLYGON_FEATURE])
        con = duckdb.connect(mem_db)
        ensure_labels_table(con)
        label_fire_detections(con, polygons, "2026-04-19T00:00:00")
        rows = con.execute(
            "SELECT label FROM fire_labels WHERE latitude = 37.77"
        ).fetchall()
        con.close()
        assert len(rows) == 1
        assert rows[0][0] == 1

    def test_tc20_point_outside_perimeter_gets_label_0(self, mem_db):
        """TC-20: LA detection outside polygon → label = 0."""
        polygons = build_shapely_polygons([SF_POLYGON_FEATURE])
        con = duckdb.connect(mem_db)
        ensure_labels_table(con)
        label_fire_detections(con, polygons, "2026-04-19T00:00:00")
        rows = con.execute(
            "SELECT label FROM fire_labels WHERE latitude = 34.05"
        ).fetchall()
        con.close()
        assert len(rows) == 1
        assert rows[0][0] == 0

    def test_tc21_skips_already_labeled_points(self, mem_db):
        """TC-21: Second call with same detections inserts 0 new rows."""
        polygons = build_shapely_polygons([SF_POLYGON_FEATURE])
        con = duckdb.connect(mem_db)
        ensure_labels_table(con)
        count1 = label_fire_detections(con, polygons, "2026-04-19T00:00:00")
        count2 = label_fire_detections(con, polygons, "2026-04-19T01:00:00")
        con.close()
        assert count1 == 2
        assert count2 == 0


# ---------------------------------------------------------------------------
# Integration tests: ingest_nifc (TC-22, TC-23)
# ---------------------------------------------------------------------------


class TestIngestNifc:
    def test_tc22_happy_path_returns_correct_summary(self, mem_db):
        """TC-22: Full ingest returns summary with correct counts."""
        with (
            patch("ai_wildfire_tracker.ingest.nifc.DB_PATH", mem_db),
            patch(
                "ai_wildfire_tracker.ingest.nifc.SESSION.get",
                return_value=_make_mock_response({"features": [SF_POLYGON_FEATURE]}),
            ),
        ):
            summary = ingest_nifc()

        assert summary["perimeters_inserted"] == 1
        assert summary["detections_labeled"] == 2
        assert summary["positive_labels"] == 1

    def test_tc23_missing_db_raises(self, tmp_path):
        """TC-23: Missing DB file raises FileNotFoundError."""
        missing = str(tmp_path / "nonexistent.db")
        with patch("ai_wildfire_tracker.ingest.nifc.DB_PATH", missing), pytest.raises(
            FileNotFoundError
        ):
            ingest_nifc()

    def test_empty_perimeters_labels_all_zero(self, mem_db):
        """Empty NIFC response → all detections labeled 0, no crash."""
        with (
            patch("ai_wildfire_tracker.ingest.nifc.DB_PATH", mem_db),
            patch(
                "ai_wildfire_tracker.ingest.nifc.SESSION.get",
                return_value=_make_mock_response({"features": []}),
            ),
        ):
            summary = ingest_nifc()

        assert summary["perimeters_inserted"] == 0
        assert summary["positive_labels"] == 0
