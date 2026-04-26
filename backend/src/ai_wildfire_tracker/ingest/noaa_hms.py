import logging
import os
from datetime import datetime, timezone

import duckdb
import pandas as pd
from dotenv import load_dotenv

from ai_wildfire_tracker.ingest.firms import ensure_fires_table

load_dotenv()
NOAA_HMS_CSV_URL = os.getenv("NOAA_HMS_CSV_URL")
DB_PATH = os.getenv("DB_PATH", "wildfire.db")
NOAA_HMS_CONFIDENCE_DEFAULT = os.getenv("NOAA_HMS_CONFIDENCE_DEFAULT", "medium")
US_BOUNDS = {
    "min_lat": 24.0,
    "max_lat": 49.5,
    "min_lon": -125.0,
    "max_lon": -66.5,
}

logger = logging.getLogger(__name__)


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lowered: dict[str, str] = {str(c).lower(): str(c) for c in df.columns}
    for name in candidates:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None


def _normalize_confidence(value: object) -> str:
    normalized = str(value or NOAA_HMS_CONFIDENCE_DEFAULT).strip().lower()
    if normalized in {"h", "high"}:
        return "high"
    if normalized in {"l", "low"}:
        return "low"
    if normalized in {"n", "nominal", "medium", "med"}:
        return "nominal"
    return normalized


def _normalize_noaa_hms(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=lambda c: str(c).strip())

    lat_col = _find_column(df, ["latitude", "lat", "y"])
    lon_col = _find_column(df, ["longitude", "lon", "long", "x"])
    bright_col = _find_column(df, ["bright_ti4", "brightness", "temp", "temperature"])
    frp_col = _find_column(df, ["frp", "power", "fire_radiative_power"])
    conf_col = _find_column(df, ["confidence", "conf", "confidence_text"])
    date_col = _find_column(df, ["acq_date", "date", "utc_date"])
    time_col = _find_column(df, ["acq_time", "time", "utc_time"])
    dt_col = _find_column(df, ["acq_datetime", "datetime", "timestamp", "date_time"])
    yearday_col = _find_column(df, ["yearday", "year_day", "julian_day"])

    if not lat_col or not lon_col:
        raise ValueError("NOAA HMS payload must include latitude/longitude columns")

    if not date_col and dt_col:
        parsed = pd.to_datetime(df[dt_col], errors="coerce", utc=False)
        df = df.copy()
        df["__acq_date"] = parsed.dt.strftime("%Y-%m-%d")
        df["__acq_time"] = parsed.dt.strftime("%H%M")
        date_col = "__acq_date"
        time_col = "__acq_time"

    if not date_col and yearday_col:
        parsed_yearday = pd.to_datetime(
            df[yearday_col].astype(str).str.strip(), format="%Y%j", errors="coerce"
        )
        df = df.copy()
        df["__acq_date"] = parsed_yearday.dt.strftime("%Y-%m-%d")
        date_col = "__acq_date"

    if not date_col:
        raise ValueError("NOAA HMS payload must include acq_date/date or datetime")
    if not time_col:
        df = df.copy()
        df["__acq_time"] = "0000"
        time_col = "__acq_time"

    normalized = pd.DataFrame(
        {
            "latitude": pd.to_numeric(df[lat_col], errors="coerce"),
            "longitude": pd.to_numeric(df[lon_col], errors="coerce"),
            "bright_ti4": pd.to_numeric(df[bright_col], errors="coerce") if bright_col else 0.0,
            "bright_ti5": None,
            "frp": pd.to_numeric(df[frp_col], errors="coerce") if frp_col else 0.0,
            "acq_date": df[date_col].astype(str),
            "acq_time": df[time_col].astype(str).str.replace(":", "", regex=False).str.zfill(4),
            "confidence": (
                df[conf_col].apply(_normalize_confidence)
                if conf_col
                else _normalize_confidence(NOAA_HMS_CONFIDENCE_DEFAULT)
            ),
        }
    )

    normalized = normalized.dropna(subset=["latitude", "longitude"])
    normalized = normalized[
        normalized["latitude"].between(US_BOUNDS["min_lat"], US_BOUNDS["max_lat"])
        & normalized["longitude"].between(US_BOUNDS["min_lon"], US_BOUNDS["max_lon"])
    ]
    normalized["acq_date"] = normalized["acq_date"].replace(
        {"NaT": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
    )
    normalized["acq_time"] = normalized["acq_time"].replace({"nan": "0000", "None": "0000"})
    return normalized


def ingest_noaa_hms() -> None:
    if not NOAA_HMS_CSV_URL:
        raise RuntimeError("Missing NOAA_HMS_CSV_URL in environment")

    logger.info("Fetching NOAA HMS data...")
    source_df = pd.read_csv(NOAA_HMS_CSV_URL)
    normalized = _normalize_noaa_hms(source_df)

    con = duckdb.connect(DB_PATH)
    try:
        ensure_fires_table(con)
        row = con.execute("SELECT COUNT(*) FROM fires").fetchone()
        count_before = row[0] if row is not None else 0
        con.execute(
            """
            INSERT INTO fires
            SELECT d.* FROM normalized d
            WHERE NOT EXISTS (
                SELECT 1 FROM fires f
                WHERE f.latitude = d.latitude
                  AND f.longitude = d.longitude
                  AND f.acq_date = d.acq_date
                  AND f.acq_time = d.acq_time
            )
            """
        )
        row = con.execute("SELECT COUNT(*) FROM fires").fetchone()
        inserted = (row[0] if row is not None else 0) - count_before
        logger.info(
            "Inserted %d new NOAA HMS records (skipped %d duplicates) into %s",
            inserted,
            len(normalized) - inserted,
            DB_PATH,
        )
    finally:
        con.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    ingest_noaa_hms()
