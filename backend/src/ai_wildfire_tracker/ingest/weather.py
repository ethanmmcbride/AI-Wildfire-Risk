"""
weather.py — NWS weather ingestor

Fetches wind speed, relative humidity, and temperature for each fire detection
point using the NOAA/NWS Gridpoint Forecast API (no API key required for
read-only forecast endpoints; set NWS_USER_AGENT in .env per NWS policy).

NWS API docs: https://www.weather.gov/documentation/services-web-api

Table created: weather_observations
Schema:
    latitude        DOUBLE   — snapped to NWS grid center
    longitude       DOUBLE   — snapped to NWS grid center
    obs_date        VARCHAR  — YYYY-MM-DD (matches fires.acq_date)
    wind_speed_kmh  DOUBLE   — wind speed in km/h
    humidity_pct    DOUBLE   — relative humidity 0–100
    temp_c          DOUBLE   — temperature in Celsius
    fetched_at      VARCHAR  — ISO timestamp of ingest run
"""

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, cast

import duckdb
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "wildfire.db")
# NWS requires a User-Agent header identifying your app + contact email.
# Set NWS_USER_AGENT="ai-wildfire-tracker/1.0 (your@email.com)" in .env
NWS_USER_AGENT = os.getenv("NWS_USER_AGENT", "ai-wildfire-tracker/1.0 (contact@example.com)")
# Seconds to wait between NWS calls to respect their rate limits (~1 req/sec)
NWS_RATE_LIMIT_SLEEP = float(os.getenv("NWS_RATE_LIMIT_SLEEP", "1.1"))
# How many unique grid cells to fetch per run (each cell = 1 NWS API call)
NWS_MAX_POINTS = int(os.getenv("NWS_MAX_POINTS", "50"))

US_BOUNDS = {
    "min_lat": 24.0,
    "max_lat": 48.5,
    "min_lon": -125.0,
    "max_lon": -66.5,
}

logger = logging.getLogger(__name__)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": NWS_USER_AGENT, "Accept": "application/geo+json"})


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


def ensure_weather_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS weather_observations (
            latitude       DOUBLE,
            longitude      DOUBLE,
            obs_date       VARCHAR,
            wind_speed_kmh DOUBLE,
            humidity_pct   DOUBLE,
            temp_c         DOUBLE,
            fetched_at     VARCHAR
        )
        """
    )


# ---------------------------------------------------------------------------
# NWS API helpers
# ---------------------------------------------------------------------------


def _nws_get(url: str) -> dict | None:
    """GET a NWS endpoint, return parsed JSON or None on failure."""
    try:
        resp = SESSION.get(url, timeout=10)
        resp.raise_for_status()
        return cast(dict[str, Any], resp.json())
    except requests.RequestException as exc:
        logger.warning("NWS request failed for %s: %s", url, exc)
        return None


def get_nws_gridpoint(lat: float, lon: float) -> tuple[str, str, str] | None:
    """
    Resolve (lat, lon) to a NWS (office, gridX, gridY) tuple.
    Returns None if the point is outside NWS coverage (e.g. offshore).
    """
    data = _nws_get(f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}")
    if not data:
        return None
    try:
        props = data["properties"]
        return props["gridId"], str(props["gridX"]), str(props["gridY"])
    except KeyError:
        logger.warning("Unexpected NWS points response for %.4f,%.4f", lat, lon)
        return None


def get_nws_forecast(office: str, grid_x: str, grid_y: str) -> dict | None:
    """
    Fetch the hourly gridpoint forecast for a resolved NWS grid cell.
    Returns the 'properties' dict or None on failure.
    """
    url = f"https://api.weather.gov/gridpoints/{office}/{grid_x},{grid_y}/forecast/hourly"
    data = _nws_get(url)
    if not data:
        return None
    return data.get("properties")


def _extract_current_conditions(props: dict) -> dict | None:
    """
    Pull the first (most current) period from a NWS hourly forecast response
    and return a flat dict with wind_speed_kmh, humidity_pct, temp_c.
    """
    periods = props.get("periods", [])
    if not periods:
        return None
    p = periods[0]

    # Wind speed: NWS returns "15 mph" or "15 km/h" strings
    wind_raw = p.get("windSpeed", "0 mph")
    try:
        wind_val = float(str(wind_raw).split()[0])
        wind_unit = str(wind_raw).split()[-1].lower() if len(str(wind_raw).split()) > 1 else "mph"
        wind_kmh = wind_val * 1.60934 if wind_unit == "mph" else wind_val
    except (ValueError, IndexError):
        wind_kmh = 0.0

    # Temperature: NWS returns Fahrenheit by default
    temp_f = float(p.get("temperature", 0) or 0)
    temp_c = round((temp_f - 32) * 5 / 9, 1)

    # Relative humidity (available in newer NWS responses)
    humidity = p.get("relativeHumidity", {})
    humidity_pct = float(humidity.get("value", 0) or 0) if isinstance(humidity, dict) else 0.0

    return {
        "wind_speed_kmh": round(wind_kmh, 2),
        "humidity_pct": round(humidity_pct, 1),
        "temp_c": temp_c,
    }


# ---------------------------------------------------------------------------
# Dedup: skip grid cells already fetched today
# ---------------------------------------------------------------------------


def _already_fetched_today(
    con: duckdb.DuckDBPyConnection, lat: float, lon: float, today: str
) -> bool:
    try:
        result = con.execute(
            """
            SELECT COUNT(*) FROM weather_observations
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


def ingest_weather(limit: int = NWS_MAX_POINTS) -> int:
    """
    For each unique fire detection point in the fires table (up to `limit`),
    fetch current NWS weather conditions and store in weather_observations.

    Returns the number of new rows inserted.
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found: {DB_PATH}. Run FIRMS ingest first.")

    con = duckdb.connect(DB_PATH)
    ensure_weather_table(con)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fetched_at = datetime.now(timezone.utc).isoformat()

    # Pull unique lat/lon points from recent fire detections
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
        logger.info("No fire points found in DB — nothing to enrich with weather")
        con.close()
        return 0

    logger.info("Fetching NWS weather for up to %d unique grid points", len(points_df))
    rows = []

    for _, row in points_df.iterrows():
        lat, lon = float(row["lat"]), float(row["lon"])

        if _already_fetched_today(con, lat, lon, today):
            logger.debug("Skipping already-fetched point %.2f,%.2f", lat, lon)
            continue

        gridpoint = get_nws_gridpoint(lat, lon)
        if not gridpoint:
            logger.debug("No NWS gridpoint for %.2f,%.2f (likely offshore)", lat, lon)
            time.sleep(NWS_RATE_LIMIT_SLEEP)
            continue

        office, grid_x, grid_y = gridpoint
        time.sleep(NWS_RATE_LIMIT_SLEEP)  # respect NWS rate limit

        props = get_nws_forecast(office, grid_x, grid_y)
        if not props:
            time.sleep(NWS_RATE_LIMIT_SLEEP)
            continue

        conditions = _extract_current_conditions(props)
        if not conditions:
            continue

        rows.append(
            {
                "latitude": lat,
                "longitude": lon,
                "obs_date": today,
                "wind_speed_kmh": conditions["wind_speed_kmh"],
                "humidity_pct": conditions["humidity_pct"],
                "temp_c": conditions["temp_c"],
                "fetched_at": fetched_at,
            }
        )
        logger.info(
            "Fetched %.2f,%.2f → wind=%.1f km/h  hum=%.0f%%  temp=%.1f°C",
            lat,
            lon,
            conditions["wind_speed_kmh"],
            conditions["humidity_pct"],
            conditions["temp_c"],
        )
        time.sleep(NWS_RATE_LIMIT_SLEEP)

    if rows:
        weather_df = pd.DataFrame(rows)  # noqa: F841 — DuckDB references this by name
        con.execute("INSERT INTO weather_observations SELECT * FROM weather_df")
        logger.info("Inserted %d weather rows into %s", len(rows), DB_PATH)
    else:
        logger.info("No new weather rows to insert")

    con.close()
    return len(rows)


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    inserted = ingest_weather()
    print(f"Done — inserted {inserted} weather observations")
