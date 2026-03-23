import duckdb
import pandas as pd
import pytest

from ai_wildfire_tracker.ingest import noaa_hms


def test_normalize_noaa_hms_with_datetime_column():
    source = pd.DataFrame(
        {
            "LATITUDE": [34.1],
            "LONGITUDE": [-118.2],
            "BRIGHTNESS": [333.7],
            "POWER": [25.4],
            "datetime": ["2024-05-01T14:30:00"],
            "CONFIDENCE": ["high"],
        }
    )

    normalized = noaa_hms._normalize_noaa_hms(source)

    assert list(normalized.columns) == [
        "latitude",
        "longitude",
        "bright_ti4",
        "bright_ti5",
        "frp",
        "acq_date",
        "acq_time",
        "confidence",
    ]
    assert len(normalized) == 1
    assert normalized.iloc[0]["latitude"] == 34.1
    assert normalized.iloc[0]["longitude"] == -118.2
    assert normalized.iloc[0]["bright_ti4"] == 333.7
    assert normalized.iloc[0]["frp"] == 25.4
    assert normalized.iloc[0]["confidence"] == "high"
    assert normalized.iloc[0]["acq_date"] == "2024-05-01"
    assert normalized.iloc[0]["acq_time"] == "1430"


def test_normalize_noaa_hms_with_yearday_column():
    source = pd.DataFrame(
        {
            "lat": [36.7],
            "lon": [-119.7],
            "temp": [333.0],
            "power": [22.0],
            "conf": ["med"],
            "yearday": [2024153],
        }
    )

    normalized = noaa_hms._normalize_noaa_hms(source)

    assert len(normalized) == 1
    row = normalized.iloc[0]
    assert row["latitude"] == 36.7
    assert row["longitude"] == -119.7
    assert row["bright_ti4"] == 333.0
    assert row["frp"] == 22.0
    assert row["confidence"] == "nominal"
    assert row["acq_date"] == "2024-06-01"
    assert row["acq_time"] == "0000"


def test_normalize_noaa_hms_filters_out_of_bounds_rows():
    source = pd.DataFrame(
        {
            "latitude": [34.0, 10.0],
            "longitude": [-118.0, -70.0],
            "brightness": [350.0, 280.0],
            "frp": [40.0, 5.0],
            "date": ["2024-06-01", "2024-06-01"],
            "time": ["1200", "0500"],
        }
    )

    normalized = noaa_hms._normalize_noaa_hms(source)

    assert len(normalized) == 1
    assert normalized.iloc[0]["latitude"] == 34.0
    assert normalized.iloc[0]["longitude"] == -118.0


def test_normalize_noaa_hms_requires_lat_lon():
    source = pd.DataFrame(
        {
            "brightness": [350.0],
            "date": ["2024-06-01"],
            "time": ["1200"],
        }
    )

    with pytest.raises(ValueError, match="latitude/longitude"):
        noaa_hms._normalize_noaa_hms(source)


def test_ingest_noaa_hms_inserts_normalized_rows(monkeypatch, tmp_path):
    db_path = tmp_path / "noaa.db"
    source = pd.DataFrame(
        {
            "lat": [36.0, None, 48.5],
            "lon": [-120.0, -121.0, -10.0],
            "temperature": [310.0, 299.0, 330.0],
            "frp": [9.5, 3.0, 22.0],
            "acq_date": ["2024-02-01", "2024-02-01", "2024-02-01"],
            "acq_time": ["0915", "0930", "1015"],
        }
    )

    monkeypatch.setattr(noaa_hms, "DB_PATH", str(db_path))
    monkeypatch.setattr(noaa_hms, "NOAA_HMS_CSV_URL", "https://example.test/noaa.csv")
    monkeypatch.setattr(noaa_hms.pd, "read_csv", lambda _: source)

    noaa_hms.ingest_noaa_hms()

    con = duckdb.connect(str(db_path))
    rows = con.execute(
        """
        SELECT latitude, longitude, bright_ti4, frp, acq_date, acq_time, confidence
        FROM fires
        ORDER BY acq_date, acq_time
        """
    ).fetchall()
    con.close()

    assert len(rows) == 1
    assert rows[0][0] == 36.0
    assert rows[0][1] == -120.0
    assert rows[0][2] == 310.0
    assert rows[0][3] == 9.5
    assert rows[0][4] == "2024-02-01"
    assert rows[0][5] == "0915"
    assert rows[0][6] == "nominal"


def test_ingest_noaa_hms_requires_url(monkeypatch):
    monkeypatch.setattr(noaa_hms, "NOAA_HMS_CSV_URL", None)

    with pytest.raises(RuntimeError, match="NOAA_HMS_CSV_URL"):
        noaa_hms.ingest_noaa_hms()
