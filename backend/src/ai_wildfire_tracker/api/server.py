# Sprint 2 Resubmission: Tomphaeton Phu: aded unhandled api parameter (region): Lines 69 - 74
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
    "min_lat": 24.0,
    "max_lat": 49.5,
    "min_lon": -125.0,
    "max_lon": -66.5,
}
CA_BOUNDS = {
    "min_lat": 32.5,
    "max_lat": 42.1,
    "min_lon": -124.5,
    "max_lon": -114.0,
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

    valid_regions = ["ca", "us", None]
    if region and region.lower() not in valid_regions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid region parameter: {region}. Valid options are: {valid_regions}",
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

        if region and region.lower() == "ca":
            where_clauses.extend(
                [
                    "latitude BETWEEN ? AND ?",
                    "longitude BETWEEN ? AND ?",
                ]
            )
            params.extend(
                [
                    CA_BOUNDS["min_lat"],
                    CA_BOUNDS["max_lat"],
                    CA_BOUNDS["min_lon"],
                    CA_BOUNDS["max_lon"],
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
