import logging
import os

import duckdb
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# MODIFIED: Allow env var override for testing
DB_PATH = os.getenv("TEST_DB_PATH", os.getenv("DB_PATH", "wildfire.db"))
US_BOUNDS = {
    "min_lat": 18.9,  # Hawaii southern tip
    "max_lat": 72.0,  # Alaska northern tip
    "min_lon": -180.0,  # Alaska western edge
    "max_lon": -66.5,  # Continental eastern edge
}
CA_BOUNDS = {
    "min_lat": 32.5,
    "max_lat": 42.1,
    "min_lon": -124.5,
    "max_lon": -114.0,
}

# All 50 US states with geographic bounds
STATE_BOUNDS = {
    "al": {"min_lat": 30.0, "max_lat": 35.0, "min_lon": -88.5, "max_lon": -84.9},
    "ak": {"min_lat": 51.0, "max_lat": 72.0, "min_lon": -180.0, "max_lon": -132.0},
    "az": {"min_lat": 31.3, "max_lat": 37.0, "min_lon": -114.8, "max_lon": -109.0},
    "ar": {"min_lat": 33.0, "max_lat": 36.5, "min_lon": -94.4, "max_lon": -89.6},
    "ca": {"min_lat": 32.5, "max_lat": 42.1, "min_lon": -124.5, "max_lon": -114.0},
    "co": {"min_lat": 37.0, "max_lat": 41.0, "min_lon": -109.1, "max_lon": -102.0},
    "ct": {"min_lat": 41.1, "max_lat": 42.1, "min_lon": -73.7, "max_lon": -71.8},
    "de": {"min_lat": 38.4, "max_lat": 39.8, "min_lon": -75.8, "max_lon": -75.0},
    "fl": {"min_lat": 24.5, "max_lat": 30.7, "min_lon": -87.6, "max_lon": -80.0},
    "ga": {"min_lat": 30.4, "max_lat": 35.0, "min_lon": -85.6, "max_lon": -80.8},
    "hi": {"min_lat": 18.9, "max_lat": 22.2, "min_lon": -160.2, "max_lon": -154.8},
    "id": {"min_lat": 42.0, "max_lat": 49.0, "min_lon": -117.2, "max_lon": -111.0},
    "il": {"min_lat": 37.0, "max_lat": 42.5, "min_lon": -91.5, "max_lon": -87.0},
    "in": {"min_lat": 37.8, "max_lat": 41.8, "min_lon": -88.1, "max_lon": -84.8},
    "ia": {"min_lat": 40.4, "max_lat": 43.5, "min_lon": -96.6, "max_lon": -90.1},
    "ks": {"min_lat": 37.0, "max_lat": 40.0, "min_lon": -102.0, "max_lon": -94.4},
    "ky": {"min_lat": 36.5, "max_lat": 39.1, "min_lon": -89.6, "max_lon": -81.9},
    "la": {"min_lat": 29.0, "max_lat": 33.0, "min_lon": -94.0, "max_lon": -88.8},
    "me": {"min_lat": 43.0, "max_lat": 47.5, "min_lon": -71.1, "max_lon": -66.9},
    "md": {"min_lat": 37.9, "max_lat": 39.7, "min_lon": -79.5, "max_lon": -75.0},
    "ma": {"min_lat": 41.2, "max_lat": 42.9, "min_lon": -73.5, "max_lon": -70.0},
    "mi": {"min_lat": 41.7, "max_lat": 48.3, "min_lon": -90.4, "max_lon": -83.0},
    "mn": {"min_lat": 43.5, "max_lat": 49.4, "min_lon": -97.2, "max_lon": -89.4},
    "ms": {"min_lat": 30.2, "max_lat": 35.0, "min_lon": -91.7, "max_lon": -88.1},
    "mo": {"min_lat": 36.5, "max_lat": 40.6, "min_lon": -95.8, "max_lon": -89.1},
    "mt": {"min_lat": 45.0, "max_lat": 49.0, "min_lon": -116.0, "max_lon": -104.0},
    "ne": {"min_lat": 40.0, "max_lat": 43.0, "min_lon": -104.0, "max_lon": -95.3},
    "nv": {"min_lat": 35.0, "max_lat": 42.0, "min_lon": -120.0, "max_lon": -114.0},
    "nh": {"min_lat": 42.7, "max_lat": 45.3, "min_lon": -72.6, "max_lon": -70.7},
    "nj": {"min_lat": 38.9, "max_lat": 41.4, "min_lon": -75.6, "max_lon": -73.9},
    "nm": {"min_lat": 31.8, "max_lat": 37.0, "min_lon": -109.0, "max_lon": -103.0},
    "ny": {"min_lat": 40.5, "max_lat": 45.0, "min_lon": -79.8, "max_lon": -71.8},
    "nc": {"min_lat": 33.8, "max_lat": 36.6, "min_lon": -84.3, "max_lon": -75.4},
    "nd": {"min_lat": 45.9, "max_lat": 49.0, "min_lon": -104.0, "max_lon": -96.6},
    "oh": {"min_lat": 38.4, "max_lat": 42.0, "min_lon": -84.8, "max_lon": -80.5},
    "ok": {"min_lat": 33.6, "max_lat": 37.0, "min_lon": -103.0, "max_lon": -94.4},
    "or": {"min_lat": 42.0, "max_lat": 46.3, "min_lon": -124.6, "max_lon": -116.5},
    "pa": {"min_lat": 39.7, "max_lat": 42.3, "min_lon": -80.5, "max_lon": -74.7},
    "ri": {"min_lat": 41.1, "max_lat": 42.0, "min_lon": -71.9, "max_lon": -71.1},
    "sc": {"min_lat": 32.0, "max_lat": 35.2, "min_lon": -83.4, "max_lon": -78.5},
    "sd": {"min_lat": 42.5, "max_lat": 45.9, "min_lon": -104.1, "max_lon": -96.4},
    "tn": {"min_lat": 35.0, "max_lat": 36.7, "min_lon": -90.3, "max_lon": -81.6},
    "tx": {"min_lat": 25.8, "max_lat": 36.5, "min_lon": -106.6, "max_lon": -93.5},
    "ut": {"min_lat": 37.0, "max_lat": 42.0, "min_lon": -114.0, "max_lon": -109.0},
    "vt": {"min_lat": 42.7, "max_lat": 45.0, "min_lon": -73.4, "max_lon": -71.4},
    "va": {"min_lat": 36.5, "max_lat": 39.5, "min_lon": -83.7, "max_lon": -75.2},
    "wa": {"min_lat": 45.6, "max_lat": 49.0, "min_lon": -124.7, "max_lon": -116.9},
    "wv": {"min_lat": 37.2, "max_lat": 40.6, "min_lon": -82.6, "max_lon": -77.7},
    "wi": {"min_lat": 42.5, "max_lat": 47.3, "min_lon": -92.9, "max_lon": -86.8},
    "wy": {"min_lat": 41.0, "max_lat": 45.0, "min_lon": -111.1, "max_lon": -104.8},
}


def compute_risk(brightness: float | None, frp: float | None) -> float:
    b = float(brightness or 0.0)
    f = float(frp or 0.0)
    return round((b * 0.6) + (f * 0.4), 2)


@app.get("/")
def root():
    return {"message": "AI Wildfire Tracker API is running"}


@app.get("/health")
def health():
    db_exists = os.path.exists(DB_PATH)
    logger.info("Health check requested. db_exists=%s db_path=%s", db_exists, DB_PATH)
    return {
        "status": "ok",
        "database_exists": db_exists,
        "db_path": DB_PATH,
    }


@app.get("/fires")
def get_fires(
    confidence: str | None = Query(default=None, description="Filter by confidence"),
    region: str | None = Query(default=None, description="Region filter, e.g. 'ca'"),
):
    logger.info("GET /fires requested with confidence=%s region=%s", confidence, region)

    valid_regions = list(STATE_BOUNDS.keys()) + ["us", None]
    if region is not None and region.lower() not in valid_regions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid region '{region}'. Must be one of: {', '.join(sorted(STATE_BOUNDS.keys()))} or 'us'",
        )

    if not os.path.exists(DB_PATH):
        logger.warning("Database file does not exist: %s", DB_PATH)
        return []

    con = duckdb.connect(DB_PATH)
    try:
        query = """
            SELECT latitude, longitude, bright_ti4, frp, confidence, acq_date, acq_time
            FROM fires
        """
        params: list[object] = []
        where_clauses: list[str] = [
            "latitude BETWEEN ? AND ?",
            "longitude BETWEEN ? AND ?",
        ]
        params.extend(
            [
                US_BOUNDS["min_lat"],
                US_BOUNDS["max_lat"],
                US_BOUNDS["min_lon"],
                US_BOUNDS["max_lon"],
            ]
        )

        if confidence:
            where_clauses.append("lower(confidence) = lower(?)")
            params.append(confidence)

        if region and region.lower() != "us":
            region_lower = region.lower()
            if region_lower in STATE_BOUNDS:
                bounds = STATE_BOUNDS[region_lower]
                where_clauses.extend(
                    [
                        "latitude BETWEEN ? AND ?",
                        "longitude BETWEEN ? AND ?",
                    ]
                )
                params.extend(
                    [
                        bounds["min_lat"],
                        bounds["max_lat"],
                        bounds["min_lon"],
                        bounds["max_lon"],
                    ]
                )

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += """
            ORDER BY acq_date DESC, acq_time DESC
            LIMIT 1000
        """

        rows = con.execute(query, params).fetchall()
        logger.info("Fetched %d fire rows", len(rows))

    except duckdb.CatalogException:
        logger.warning("Table 'fires' does not exist yet")
        return []
    except Exception:
        logger.exception("Unexpected error while reading fires")
        raise
    finally:
        con.close()

    return [
        {
            "lat": r[0],
            "lon": r[1],
            "brightness": r[2],
            "frp": r[3],
            "confidence": r[4],
            "acq_date": r[5],
            "acq_time": r[6],
            "risk": compute_risk(r[2], r[3]),
        }
        for r in rows
    ]
