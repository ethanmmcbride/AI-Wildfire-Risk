"""
nifc.py — NIFC fire perimeter ingestor for AI Wildfire Tracker
backend/src/ai_wildfire_tracker/ingest/nifc.py

Downloads WFIGS current interagency fire perimeters from the NIFC ArcGIS
REST API and performs a spatial join against FIRMS fire detection points
to assign binary training labels for the Random Forest model.

Label definition:
    1 = a NIFC fire perimeter overlaps this detection point (fire confirmed)
    0 = no perimeter overlap (no confirmed fire at this point)

NIFC ArcGIS REST endpoint (no API key required, public domain):
    https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/
    WFIGS_Interagency_Perimeters_Current/FeatureServer/0/query

Verified working Postman call (2026-04-19):
    GET .../query?where=1%3D1&outFields=poly_IncidentName,poly_GISAcres,
    poly_CreateDate&returnGeometry=true&outSR=4326&f=geojson&resultRecordCount=5

Tables created:
    fire_perimeters — raw perimeter polygons (GeoJSON geometry as string)
    fire_labels     — one row per FIRMS detection with label 0 or 1
"""

import json
import logging
import os
from datetime import datetime, timezone

import duckdb
import pandas as pd
import requests
from dotenv import load_dotenv
from shapely.geometry import Point, shape

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "wildfire.db")

NIFC_URL = (
    "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services"
    "/WFIGS_Interagency_Perimeters_Current/FeatureServer/0/query"
)

US_BOUNDS = {
    "min_lat": 24.0,
    "max_lat": 49.5,
    "min_lon": -125.0,
    "max_lon": -66.5,
}

NIFC_MAX_FEATURES = int(os.getenv("NIFC_MAX_FEATURES", "1000"))

logger = logging.getLogger(__name__)

SESSION = requests.Session()
SESSION.headers.update({"Accept": "application/json"})


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------


def ensure_perimeter_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS fire_perimeters (
            incident_name VARCHAR,
            gis_acres     DOUBLE,
            create_date   VARCHAR,
            geometry_json VARCHAR,
            fetched_at    VARCHAR
        )
        """
    )


def ensure_labels_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS fire_labels (
            latitude   DOUBLE,
            longitude  DOUBLE,
            acq_date   VARCHAR,
            label      INTEGER,
            labeled_at VARCHAR
        )
        """
    )


# ---------------------------------------------------------------------------
# NIFC API helpers
# ---------------------------------------------------------------------------


def fetch_nifc_perimeters(max_features: int = NIFC_MAX_FEATURES) -> list[dict]:
    """
    Fetch current fire perimeter GeoJSON features from NIFC ArcGIS REST API.
    Returns a list of GeoJSON feature dicts, empty list on failure.
    """
    params = {
        "where": "1=1",
        "outFields": "poly_IncidentName,poly_GISAcres,poly_CreateDate",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
        "resultRecordCount": max_features,
    }

    try:
        resp = SESSION.get(NIFC_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.error("NIFC request failed: %s", exc)
        return []

    if "error" in data:
        logger.error("NIFC API error: %s", data["error"])
        return []

    features = data.get("features", [])
    logger.info("Fetched %d NIFC perimeter features", len(features))
    return features


def store_perimeters(
    con: duckdb.DuckDBPyConnection, features: list[dict], fetched_at: str
) -> int:
    """Store raw perimeter features in fire_perimeters table. Returns count inserted."""
    if not features:
        return 0

    rows = []
    for f in features:
        props = f.get("properties", {})
        rows.append(
            {
                "incident_name": str(props.get("poly_IncidentName") or ""),
                "gis_acres": float(props.get("poly_GISAcres") or 0.0),
                "create_date": str(props.get("poly_CreateDate") or ""),
                "geometry_json": json.dumps(f.get("geometry", {})),
                "fetched_at": fetched_at,
            }
        )

    perimeters_df = pd.DataFrame(rows)  # noqa: F841 — DuckDB references by name
    con.execute("INSERT INTO fire_perimeters SELECT * FROM perimeters_df")
    return len(rows)


# ---------------------------------------------------------------------------
# Spatial join helpers
# ---------------------------------------------------------------------------


def build_shapely_polygons(features: list[dict]) -> list:
    """Convert GeoJSON feature list to valid Shapely geometry objects."""
    polygons = []
    for f in features:
        try:
            geom = shape(f["geometry"])
            if geom.is_valid:
                polygons.append(geom)
        except Exception as exc:
            logger.debug("Skipping invalid geometry: %s", exc)
    return polygons


def point_in_any_perimeter(lat: float, lon: float, polygons: list) -> bool:
    """Return True if (lat, lon) falls inside any perimeter polygon."""
    pt = Point(lon, lat)  # Shapely uses (lon, lat) order
    return any(poly.contains(pt) for poly in polygons)


def label_fire_detections(
    con: duckdb.DuckDBPyConnection, polygons: list, labeled_at: str
) -> int:
    """
    For each FIRMS detection in the fires table, assign label 1 if the point
    falls inside a NIFC perimeter polygon, else 0.
    Skips points already labeled. Returns count of new labeled rows inserted.
    """
    try:
        detections = con.execute(
            """
            SELECT DISTINCT
                ROUND(latitude, 2)  AS lat,
                ROUND(longitude, 2) AS lon,
                acq_date
            FROM fires
            WHERE latitude  BETWEEN ? AND ?
              AND longitude BETWEEN ? AND ?
            """,
            [
                US_BOUNDS["min_lat"],
                US_BOUNDS["max_lat"],
                US_BOUNDS["min_lon"],
                US_BOUNDS["max_lon"],
            ],
        ).df()
    except duckdb.CatalogException:
        logger.warning("fires table not found — run FIRMS ingest first")
        return 0

    if detections.empty:
        logger.info("No fire detections found to label")
        return 0

    # Load already-labeled keys to avoid duplicates
    try:
        existing = con.execute(
            "SELECT latitude, longitude, acq_date FROM fire_labels"
        ).df()
        existing_keys = set(
            zip(existing["latitude"], existing["longitude"], existing["acq_date"])
        )
    except duckdb.CatalogException:
        existing_keys = set()

    rows = []
    for _, row in detections.iterrows():
        lat = float(row["lat"])
        lon = float(row["lon"])
        acq_date = str(row["acq_date"])

        if (lat, lon, acq_date) in existing_keys:
            continue

        label = 1 if point_in_any_perimeter(lat, lon, polygons) else 0
        rows.append(
            {
                "latitude": lat,
                "longitude": lon,
                "acq_date": acq_date,
                "label": label,
                "labeled_at": labeled_at,
            }
        )

    if rows:
        labels_df = pd.DataFrame(rows)  # noqa: F841 — DuckDB references by name
        con.execute("INSERT INTO fire_labels SELECT * FROM labels_df")
        pos = sum(r["label"] for r in rows)
        logger.info(
            "Labeled %d detections: %d positive (fire), %d negative",
            len(rows),
            pos,
            len(rows) - pos,
        )

    return len(rows)


# ---------------------------------------------------------------------------
# Public ingest function
# ---------------------------------------------------------------------------


def ingest_nifc() -> dict:
    """
    Fetch NIFC current fire perimeters and label FIRMS detection points.

    Returns a summary dict:
        perimeters_inserted: int
        detections_labeled:  int
        positive_labels:     int
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}. Run FIRMS ingest first."
        )

    con = duckdb.connect(DB_PATH)
    ensure_perimeter_table(con)
    ensure_labels_table(con)

    fetched_at = datetime.now(timezone.utc).isoformat()

    features = fetch_nifc_perimeters()
    if not features:
        logger.warning("No NIFC perimeters fetched — labels will all be 0")
        con.close()
        return {"perimeters_inserted": 0, "detections_labeled": 0, "positive_labels": 0}

    perimeters_inserted = store_perimeters(con, features, fetched_at)
    polygons = build_shapely_polygons(features)
    logger.info("Built %d valid Shapely polygons for spatial join", len(polygons))

    detections_labeled = label_fire_detections(con, polygons, fetched_at)

    try:
        result = con.execute(
            "SELECT COUNT(*) FROM fire_labels WHERE label = 1"
        ).fetchone()
        positive_labels = result[0] or 0
    except duckdb.CatalogException:
        positive_labels = 0

    con.close()

    summary = {
        "perimeters_inserted": perimeters_inserted,
        "detections_labeled": detections_labeled,
        "positive_labels": positive_labels,
    }
    logger.info("NIFC ingest complete: %s", summary)
    return summary


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    summary = ingest_nifc()
    print(f"Done — {summary}")
