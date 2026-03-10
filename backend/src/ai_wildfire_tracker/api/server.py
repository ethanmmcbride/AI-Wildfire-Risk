import logging
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import duckdb
import os

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Wildfire Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# MODIFIED: Allow env var override for testing
DB_PATH = os.getenv("TEST_DB_PATH", os.getenv("DB_PATH", "wildfire.db"))

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
):
    logger.info("GET /fires requested with confidence=%s", confidence)
    # Handling if DB doesn't exist yet
    if not os.path.exists(DB_PATH):
        logger.warning("Database file does not exist: %s", DB_PATH)
        return []

    con = duckdb.connect(DB_PATH)
    try:
        query = """
            SELECT latitude, longitude, bright_ti4, frp, confidence
            FROM fires
        """
        params: list[str] = []

        if confidence:
            query += " WHERE lower(confidence) = lower(?)"
            params.append(confidence)

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
            "risk": compute_risk(r[2], r[3]),
        }
        for r in rows
    ]