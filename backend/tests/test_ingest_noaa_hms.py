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
    assert normalized.iloc[0]["latitude"] == 34.1
    assert normalized.iloc[0]["longitude"] == -118.2
    assert normalized.iloc[0]["acq_date"] == "2024-05-01"
    assert normalized.iloc[0]["acq_time"] == "1430"


def test_ingest_noaa_hms_inserts_normalized_rows(monkeypatch, tmp_path):
    db_path = tmp_path / "noaa.db"
    sample = pd.DataFrame(
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
    monkeypatch.setattr(noaa_hms.pd, "read_csv", lambda _: sample)

    noaa_hms.ingest_noaa_hms()

    con = duckdb.connect(str(db_path))
    rows = con.execute(
        """
        SELECT latitude, longitude, bright_ti4, frp, acq_date, acq_time, confidence
        FROM fires
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
