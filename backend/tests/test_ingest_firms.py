import duckdb
import pandas as pd
import pytest

from ai_wildfire_tracker.ingest import firms


def test_ensure_fires_table_creates_table(tmp_path):
    db_path = tmp_path / "firms_test.db"
    con = duckdb.connect(str(db_path))

    firms.ensure_fires_table(con)

    tables = con.execute("SHOW TABLES").fetchall()
    con.close()

    table_names = [row[0] for row in tables]
    assert "fires" in table_names


def test_ingest_firms_requires_api_key(monkeypatch):
    monkeypatch.delenv("FIRMS_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="Missing FIRMS_API_KEY"):
        firms.ingest_firms()


def test_ingest_firms_inserts_only_us_rows(monkeypatch, tmp_path):
    db_path = tmp_path / "firms_ingest.db"

    source = pd.DataFrame(
        {
            "latitude": [34.0, 36.5, 10.0],
            "longitude": [-118.0, -119.5, -70.0],
            "bright_ti4": [350.5, 320.0, 280.0],
            "bright_ti5": [300.0, 280.0, 250.0],
            "frp": [50.0, 20.0, 5.0],
            "acq_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "acq_time": ["1200", "1300", "1400"],
            "confidence": ["high", "nominal", "low"],
        }
    )

    monkeypatch.setenv("FIRMS_API_KEY", "fake-key")
    monkeypatch.setattr(firms, "DB_PATH", str(db_path))
    monkeypatch.setattr(firms.pd, "read_csv", lambda _: source)

    firms.ingest_firms()

    con = duckdb.connect(str(db_path))
    rows = con.execute(
        """
        SELECT latitude, longitude, bright_ti4, bright_ti5, frp, acq_date, acq_time, confidence
        FROM fires
        ORDER BY acq_date, acq_time
        """
    ).fetchall()
    con.close()

    assert len(rows) == 2
    assert rows[0] == (34.0, -118.0, 350.5, 300.0, 50.0, "2024-01-01", "1200", "high")
    assert rows[1] == (36.5, -119.5, 320.0, 280.0, 20.0, "2024-01-02", "1300", "nominal")


def test_ingest_firms_empty_us_result_creates_table_with_no_rows(monkeypatch, tmp_path):
    db_path = tmp_path / "firms_empty.db"

    source = pd.DataFrame(
        {
            "latitude": [10.0],
            "longitude": [-70.0],
            "bright_ti4": [280.0],
            "bright_ti5": [250.0],
            "frp": [5.0],
            "acq_date": ["2024-01-03"],
            "acq_time": ["1400"],
            "confidence": ["low"],
        }
    )

    monkeypatch.setenv("FIRMS_API_KEY", "fake-key")
    monkeypatch.setattr(firms, "DB_PATH", str(db_path))
    monkeypatch.setattr(firms.pd, "read_csv", lambda _: source)

    firms.ingest_firms()

    con = duckdb.connect(str(db_path))
    count = con.execute("SELECT COUNT(*) FROM fires").fetchone()[0]
    con.close()

    assert count == 0
