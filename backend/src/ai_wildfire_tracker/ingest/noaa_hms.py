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


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lowered = {c.lower(): c for c in df.columns}
    for name in candidates:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None


def _normalize_noaa_hms(df: pd.DataFrame) -> pd.DataFrame:
    lat_col = _find_column(df, ["latitude", "lat", "y"])
    lon_col = _find_column(df, ["longitude", "lon", "long", "x"])
    bright_col = _find_column(df, ["bright_ti4", "brightness", "temp", "temperature"])
    frp_col = _find_column(df, ["frp", "power", "fire_radiative_power"])
    conf_col = _find_column(df, ["confidence", "conf", "confidence_text"])
    date_col = _find_column(df, ["acq_date", "date", "utc_date"])
    time_col = _find_column(df, ["acq_time", "time", "utc_time"])
    dt_col = _find_column(df, ["acq_datetime", "datetime", "timestamp", "date_time"])

    if not lat_col or not lon_col:
        raise ValueError("NOAA HMS payload must include latitude/longitude columns")

    if not date_col and dt_col:
        parsed = pd.to_datetime(df[dt_col], errors="coerce", utc=False)
        df = df.copy()
        df["__acq_date"] = parsed.dt.strftime("%Y-%m-%d")
        df["__acq_time"] = parsed.dt.strftime("%H%M")
        date_col = "__acq_date"
        time_col = "__acq_time"

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
            "confidence": df[conf_col].astype(str) if conf_col else NOAA_HMS_CONFIDENCE_DEFAULT,
        }
    )

    normalized = normalized.dropna(subset=["latitude", "longitude"])
    normalized["acq_date"] = normalized["acq_date"].replace(
        {"NaT": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
    )
    normalized["acq_time"] = normalized["acq_time"].replace({"nan": "0000", "None": "0000"})
    return normalized


def ingest_noaa_hms() -> None:
    if not NOAA_HMS_CSV_URL:
        raise RuntimeError("Missing NOAA_HMS_CSV_URL in environment")

    print("Fetching NOAA HMS data...")
    source_df = pd.read_csv(NOAA_HMS_CSV_URL)
    normalized = _normalize_noaa_hms(source_df)

    con = duckdb.connect(DB_PATH)
    ensure_fires_table(con)
    con.execute("INSERT INTO fires SELECT * FROM normalized")
    con.close()

    print(f"Inserted {len(normalized)} NOAA HMS records into {DB_PATH}")


if __name__ == "__main__":
    ingest_noaa_hms()
