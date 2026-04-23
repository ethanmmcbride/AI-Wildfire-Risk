"""
firms.py — NASA FIRMS fire detection ingestor for AI Wildfire Tracker
backend/src/ai_wildfire_tracker/ingest/firms.py

Fetches VIIRS SNPP active fire detections from the NASA FIRMS API.

Two data sources:
    VIIRS_SNPP_NRT — Near Real-Time, last ~60 days, max 10 days/request
    VIIRS_SNPP_SP  — Standard Processing, historical, max 5 days/request

URL format:
    /api/area/csv/{key}/{source}/{west,south,east,north}/{day_range}/{date}
"""

import logging
import os
import time

import duckdb
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "wildfire.db")
FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

US_BOUNDS = {
    "min_lat": 24.0,
    "max_lat": 49.5,
    "min_lon": -125.0,
    "max_lon": -66.5,
}

# Bounding box in FIRMS format: west,south,east,north
US_BBOX = f"{US_BOUNDS['min_lon']},{US_BOUNDS['min_lat']},{US_BOUNDS['max_lon']},{US_BOUNDS['max_lat']}"

# Peak fire season windows — SP allows max 5 days per request.
# 6 windows covering Aug 1-30 + Sep 1-30 + Oct 1-15 of 2024.
# Each tuple: (start_date, day_range, source)
PEAK_SEASON_WINDOWS = [
    ("2024-08-01", 5, "VIIRS_SNPP_SP"),
    ("2024-08-06", 5, "VIIRS_SNPP_SP"),
    ("2024-09-01", 5, "VIIRS_SNPP_SP"),
    ("2024-09-06", 5, "VIIRS_SNPP_SP"),
    ("2024-10-01", 5, "VIIRS_SNPP_SP"),
    ("2024-10-06", 5, "VIIRS_SNPP_SP"),
]

FIRMS_RATE_LIMIT_SLEEP = float(os.getenv("FIRMS_RATE_LIMIT_SLEEP", "3.0"))

logger = logging.getLogger(__name__)

REQUIRED_COLS = [
    "latitude",
    "longitude",
    "bright_ti4",
    "bright_ti5",
    "frp",
    "acq_date",
    "acq_time",
    "confidence",
]


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------


def ensure_fires_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS fires (
            latitude   DOUBLE,
            longitude  DOUBLE,
            bright_ti4 DOUBLE,
            bright_ti5 DOUBLE,
            frp        DOUBLE,
            acq_date   VARCHAR,
            acq_time   VARCHAR,
            confidence VARCHAR
        )
        """
    )


def _count_existing(con: duckdb.DuckDBPyConnection, date: str) -> int:
    try:
        result = con.execute(
            "SELECT COUNT(*) FROM fires WHERE acq_date = ?", [date]
        ).fetchone()
        return result[0] or 0
    except duckdb.CatalogException:
        return 0


# ---------------------------------------------------------------------------
# Core fetch function
# ---------------------------------------------------------------------------


def fetch_firms_window(
    api_key: str,
    source: str = "VIIRS_SNPP_NRT",
    start_date: str | None = None,
    day_range: int = 1,
) -> pd.DataFrame:
    """
    Fetch FIRMS detections for a date window, return US-filtered DataFrame.

    Args:
        api_key:    NASA FIRMS MAP_KEY
        source:     VIIRS_SNPP_NRT (max 10 days) or VIIRS_SNPP_SP (max 5 days)
        start_date: YYYY-MM-DD for historical data, None for latest NRT
        day_range:  Days to fetch. NRT: 1-10, SP: 1-5.

    Returns:
        US-filtered DataFrame with required columns, or empty DataFrame on failure.
    """
    if start_date:
        url = f"{FIRMS_BASE}/{api_key}/{source}/{US_BBOX}/{day_range}/{start_date}"
    else:
        url = f"{FIRMS_BASE}/{api_key}/{source}/{US_BBOX}/{day_range}"

    logger.info(
        "Fetching FIRMS %s: start=%s days=%d",
        source,
        start_date or "latest",
        day_range,
    )

    try:
        df = pd.read_csv(url)
    except Exception as exc:
        logger.error(
            "FIRMS fetch failed for %s %s: %s", source, start_date or "latest", exc
        )
        return pd.DataFrame()

    if df.empty:
        logger.warning("Empty response from FIRMS for %s", start_date or "latest")
        return pd.DataFrame()

    # Keep only required columns — handle missing gracefully
    available = [c for c in REQUIRED_COLS if c in df.columns]
    if len(available) < len(REQUIRED_COLS):
        missing = set(REQUIRED_COLS) - set(available)
        logger.warning("FIRMS response missing columns: %s", missing)
        return pd.DataFrame()

    df = df[REQUIRED_COLS].copy()

    # Filter to US bounds
    df = df[
        df["latitude"].between(US_BOUNDS["min_lat"], US_BOUNDS["max_lat"])
        & df["longitude"].between(US_BOUNDS["min_lon"], US_BOUNDS["max_lon"])
    ]

    logger.info(
        "Fetched %d US detections for %s window starting %s",
        len(df),
        source,
        start_date or "latest",
    )
    return df


# ---------------------------------------------------------------------------
# Public ingest functions
# ---------------------------------------------------------------------------


def ingest_firms() -> int:
    """Ingest the most recent 1 day of NRT data. Returns rows inserted."""
    api_key = os.getenv("FIRMS_API_KEY")
    if not api_key:
        raise RuntimeError("Missing FIRMS_API_KEY in .env")

    df = fetch_firms_window(api_key, source="VIIRS_SNPP_NRT", day_range=1)
    if df.empty:
        logger.warning("No data returned from FIRMS NRT fetch")
        return 0

    con = duckdb.connect(DB_PATH)
    try:
        ensure_fires_table(con)
        con.execute("INSERT INTO fires SELECT * FROM df")
        logger.info("Inserted %d fire records into %s", len(df), DB_PATH)
        return len(df)
    finally:
        con.close()


def ingest_firms_historical(
    windows: list[tuple[str, int, str]] | None = None,
) -> int:
    """
    Ingest historical FIRMS data across peak fire season windows.
    Uses VIIRS_SNPP_SP (Standard Processing, max 5 days/request).
    Skips windows already in DB. Returns total rows inserted.
    """
    api_key = os.getenv("FIRMS_API_KEY")
    if not api_key:
        raise RuntimeError("Missing FIRMS_API_KEY in .env")

    if windows is None:
        windows = PEAK_SEASON_WINDOWS

    con = duckdb.connect(DB_PATH)
    ensure_fires_table(con)
    total_inserted = 0

    for start_date, day_range, source in windows:
        existing = _count_existing(con, start_date)
        if existing > 0:
            logger.info("Skipping %s — already have %d rows", start_date, existing)
            continue

        df = fetch_firms_window(
            api_key, source=source, start_date=start_date, day_range=day_range
        )

        if df.empty:
            logger.warning("No data for window %s", start_date)
            time.sleep(FIRMS_RATE_LIMIT_SLEEP)
            continue

        con.execute("INSERT INTO fires SELECT * FROM df")
        total_inserted += len(df)
        logger.info(
            "Inserted %d rows for %s (%d days)", len(df), start_date, day_range
        )
        time.sleep(FIRMS_RATE_LIMIT_SLEEP)

    con.close()
    logger.info("Historical ingest complete — total inserted: %d", total_inserted)
    return total_inserted


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    parser = argparse.ArgumentParser(description="NASA FIRMS ingestor")
    parser.add_argument(
        "--historical",
        action="store_true",
        help="Ingest peak fire season historical data (Aug-Oct 2024)",
    )
    args = parser.parse_args()

    if args.historical:
        total = ingest_firms_historical()
        print(f"Done — inserted {total} historical fire records")
    else:
        total = ingest_firms()
        print(f"Done — inserted {total} fire records")
