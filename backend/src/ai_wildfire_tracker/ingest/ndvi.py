"""
ndvi.py — Environmental conditions ingestor for AI Wildfire Tracker

Fetches surface-level environmental conditions for each fire detection point
using the Open-Meteo API (free, no API key required).

Variables fetched (strong wildfire risk indicators used in NFDRS):
    soil_moisture_0_to_1cm       — hourly volumetric soil water (m³/m³)
                                   Low values = dry fuel = higher ignition risk
    vapor_pressure_deficit_max   — daily VPD in kPa
                                   High VPD = vegetation stress = higher fire risk
    et0_fao_evapotranspiration   — daily reference ET in mm
                                   High ET = dry surface conditions


Open-Meteo docs: https://open-meteo.com/en/docs

Table created: environmental_conditions
Schema:
    latitude      DOUBLE
    longitude     DOUBLE
    obs_date      VARCHAR  — YYYY-MM-DD
    soil_moisture DOUBLE   — mean of 24 hourly values (m³/m³)
    vpd_kpa       DOUBLE   — vapor pressure deficit in kPa
    et0_mm        DOUBLE   — evapotranspiration in mm
    fetched_at    VARCHAR  — ISO timestamp of ingest run
"""

import logging
import os
import time
from datetime import datetime, timezone

import duckdb
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "wildfire.db")
OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_SLEEP = float(os.getenv("OPEN_METEO_SLEEP", "0.5"))
OPEN_METEO_MAX_POINTS = int(os.getenv("OPEN_METEO_MAX_POINTS", "100"))

US_BOUNDS = {
    "min_lat": 24.0,
    "max_lat": 49.5,
    "min_lon": -125.0,
    "max_lon": -66.5,
}

logger = logging.getLogger(__name__)

SESSION = requests.Session()
SESSION.headers.update({"Accept": "application/json"})


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------


def ensure_environmental_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS environmental_conditions (
            latitude      DOUBLE,
            longitude     DOUBLE,
            obs_date      VARCHAR,
            soil_moisture DOUBLE,
            vpd_kpa       DOUBLE,
            et0_mm        DOUBLE,
            fetched_at    VARCHAR
        )
        """
    )


# ---------------------------------------------------------------------------
# Open-Meteo API helper
# ---------------------------------------------------------------------------


def fetch_environmental_conditions(lat: float, lon: float) -> dict | None:
    """
    Fetch today's environmental conditions for a lat/lon point from Open-Meteo.

    Uses:
        hourly=soil_moisture_0_to_1cm       (mean of 24 hourly values)
        daily=vapor_pressure_deficit_max
        daily=et0_fao_evapotranspiration

    Returns a flat dict with soil_moisture, vpd_kpa, et0_mm or None on failure.
    """
    params: dict[str, str | float | int] = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "soil_moisture_0_to_1cm",
        "daily": "vapor_pressure_deficit_max,et0_fao_evapotranspiration",
        "timezone": "America/Los_Angeles",
        "forecast_days": 1,
    }

    try:
        resp = SESSION.get(OPEN_METEO_BASE, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("Open-Meteo request failed for %.4f,%.4f: %s", lat, lon, exc)
        return None

    try:
        # Soil moisture: mean of all 24 hourly values for today
        hourly_values = data["hourly"]["soil_moisture_0_to_1cm"]
        valid = [v for v in hourly_values if v is not None]
        soil_moisture = round(sum(valid) / len(valid), 4) if valid else 0.0

        daily = data["daily"]
        vpd_kpa = float(daily["vapor_pressure_deficit_max"][0] or 0.0)
        et0_mm = float(daily["et0_fao_evapotranspiration"][0] or 0.0)

        return {
            "soil_moisture": soil_moisture,
            "vpd_kpa": round(vpd_kpa, 3),
            "et0_mm": round(et0_mm, 3),
        }
    except (KeyError, IndexError, TypeError, ZeroDivisionError) as exc:
        logger.warning("Unexpected Open-Meteo response for %.4f,%.4f: %s", lat, lon, exc)
        return None


# ---------------------------------------------------------------------------
# Dedup: skip points already fetched today
# ---------------------------------------------------------------------------


def _already_fetched_today(
    con: duckdb.DuckDBPyConnection, lat: float, lon: float, today: str
) -> bool:
    try:
        result = con.execute(
            """
            SELECT COUNT(*) FROM environmental_conditions
            WHERE latitude = ? AND longitude = ? AND obs_date = ?
            """,
            [lat, lon, today],
        ).fetchone()
        if result is None:
            return False
        return (result[0] or 0) > 0
    except duckdb.CatalogException:
        return False


# ---------------------------------------------------------------------------
# Public ingest function
# ---------------------------------------------------------------------------


def ingest_environmental(limit: int = OPEN_METEO_MAX_POINTS) -> int:
    """
    For each unique fire detection point in the fires table (up to `limit`),
    fetch environmental conditions from Open-Meteo and store in
    environmental_conditions table.

    Returns the number of new rows inserted.
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found: {DB_PATH}. Run FIRMS ingest first.")

    con = duckdb.connect(DB_PATH)
    ensure_environmental_table(con)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fetched_at = datetime.now(timezone.utc).isoformat()

    try:
        points_df = con.execute(
            """
            SELECT DISTINCT
                ROUND(latitude, 2)  AS lat,
                ROUND(longitude, 2) AS lon
            FROM fires
            WHERE latitude  BETWEEN ? AND ?
              AND longitude BETWEEN ? AND ?
            ORDER BY lat DESC
            LIMIT ?
            """,
            [
                US_BOUNDS["min_lat"],
                US_BOUNDS["max_lat"],
                US_BOUNDS["min_lon"],
                US_BOUNDS["max_lon"],
                int(limit),
            ],
        ).df()
    except duckdb.CatalogException:
        logger.warning("fires table does not exist yet — run FIRMS ingest first")
        con.close()
        return 0

    if points_df.empty:
        logger.info("No fire points found in DB — nothing to enrich")
        con.close()
        return 0

    logger.info("Fetching Open-Meteo environmental conditions for %d points", len(points_df))
    rows = []

    for _, row in points_df.iterrows():
        lat, lon = float(row["lat"]), float(row["lon"])

        if _already_fetched_today(con, lat, lon, today):
            logger.debug("Skipping already-fetched point %.2f,%.2f", lat, lon)
            continue

        conditions = fetch_environmental_conditions(lat, lon)
        if not conditions:
            time.sleep(OPEN_METEO_SLEEP)
            continue

        rows.append(
            {
                "latitude": lat,
                "longitude": lon,
                "obs_date": today,
                "soil_moisture": conditions["soil_moisture"],
                "vpd_kpa": conditions["vpd_kpa"],
                "et0_mm": conditions["et0_mm"],
                "fetched_at": fetched_at,
            }
        )
        logger.info(
            "Fetched %.2f,%.2f → soil=%.4f  vpd=%.2f kPa  et0=%.2f mm",
            lat,
            lon,
            conditions["soil_moisture"],
            conditions["vpd_kpa"],
            conditions["et0_mm"],
        )
        time.sleep(OPEN_METEO_SLEEP)

    if rows:
        env_df = pd.DataFrame(rows)  # noqa: F841 — DuckDB references by name
        con.execute("INSERT INTO environmental_conditions SELECT * FROM env_df")
        logger.info("Inserted %d environmental rows into %s", len(rows), DB_PATH)
    else:
        logger.info("No new environmental rows to insert")

    con.close()
    return len(rows)


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    inserted = ingest_environmental()
    print(f"Done — inserted {inserted} environmental observations")
