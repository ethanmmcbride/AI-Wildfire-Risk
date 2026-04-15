import duckdb
import pytest

from ai_wildfire import configs
from ai_wildfire.data_loader import load_firms_table

EXPECTED_COLUMNS = [
    "latitude",
    "longitude",
    "bright_ti4",
    "bright_ti5",
    "frp",
    "acq_date",
    "acq_time",
    "confidence",
]


def test_load_firms_table_returns_expected_columns(seeded_golden_db):
    df = load_firms_table()
    assert list(df.columns) == EXPECTED_COLUMNS


def test_load_firms_table_returns_correct_row_count(seeded_golden_db):
    df = load_firms_table()
    assert len(df) == 50


def test_load_firms_table_respects_limit(seeded_golden_db):
    df = load_firms_table(limit=5)
    assert len(df) == 5


def test_load_firms_table_missing_db_raises(monkeypatch):
    monkeypatch.setattr(configs, "DB_PATH", "/nonexistent/path/missing.db")
    with pytest.raises((duckdb.IOException, duckdb.Error)):
        load_firms_table()
