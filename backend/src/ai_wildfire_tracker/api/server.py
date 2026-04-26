import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import duckdb
import joblib
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    _load_model()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.getenv("TEST_DB_PATH", os.getenv("DB_PATH", "wildfire.db"))

# Model path — defaults to ai/artifacts relative to project root.
# Override with MODEL_PATH env var for different environments.
_DEFAULT_MODEL_PATH = (
    Path(__file__).parent.parent.parent.parent / "ai" / "artifacts" / "baseline_model.joblib"
)
MODEL_PATH = Path(os.getenv("MODEL_PATH", str(_DEFAULT_MODEL_PATH)))

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

# ---------------------------------------------------------------------------
# Model loading — loaded once at startup, not on every request
# ---------------------------------------------------------------------------

_model = None


def _load_model():
    """
    Load the trained Random Forest model from disk.
    Called once at startup. Returns None if model file doesn't exist,
    in which case the fallback formula is used.
    """
    global _model
    if _model is not None:
        return _model

    if not MODEL_PATH.exists():
        logger.warning("RF model not found at %s — using brightness formula fallback", MODEL_PATH)
        return None

    try:
        _model = joblib.load(MODEL_PATH)
        logger.info("RF model loaded from %s", MODEL_PATH)
        return _model
    except Exception as exc:
        logger.error("Failed to load RF model: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Risk scoring
# ---------------------------------------------------------------------------

# Feature order must match FEATURE_COLS in features.py exactly
_FEATURE_ORDER = [
    "bright_ti4",
    "bright_ti5",
    "frp",
    "hour",
    "month",
    "lat_bin",
    "lon_bin",
    "wind_speed_kmh",
    "humidity_pct",
    "temp_c",
    "soil_moisture",
    "vpd_kpa",
    "et0_mm",
]


def _fallback_risk(brightness: float, frp: float) -> float:
    """
    Fallback risk formula used when RF model is unavailable.
    Returns a normalized score in [0, 1] based on brightness and FRP.
    Kept as a safety net — the RF model is always preferred.
    """
    b = float(brightness or 0.0)
    f = float(frp or 0.0)
    raw = (b * 0.6) + (f * 0.4)
    # Normalize to 0-1 range (typical max brightness ~500, frp ~200)
    return round(min(raw / 350.0, 1.0), 4)


def compute_risk_batch(rows: list, weather_map: dict, env_map: dict) -> list[float]:
    """
    Compute RF risk scores for a batch of fire rows.
    Falls back to brightness formula if model is unavailable.

    Args:
        rows: List of DB rows (lat, lon, bright_ti4, bright_ti5, frp,
              confidence, acq_date, acq_time)
        weather_map: Dict keyed by (round(lat,2), round(lon,2)) →
                     {wind_speed_kmh, humidity_pct, temp_c}
        env_map:     Dict keyed by (round(lat,2), round(lon,2)) →
                     {soil_moisture, vpd_kpa, et0_mm}

    Returns:
        List of float risk scores in [0, 1], one per row.
    """
    model = _load_model()

    if model is None:
        return [_fallback_risk(r[2], r[4]) for r in rows]

    from datetime import datetime

    features = []
    for r in rows:
        lat, lon = float(r[0]), float(r[1])
        bright_ti4 = float(r[2] or 0)
        bright_ti5 = float(r[3] or 0)
        frp = float(r[4] or 0)
        acq_date = str(r[6] or "")
        acq_time = str(r[7] or "0000").zfill(4)

        # Temporal features
        try:
            dt = datetime.strptime(f"{acq_date} {acq_time}", "%Y-%m-%d %H%M")
            hour = dt.hour
            month = dt.month
        except ValueError:
            hour, month = 0, 0

        # Spatial bins
        lat_bin = int(lat // 1)
        lon_bin = int(lon // 1)

        # Weather features — look up by rounded lat/lon
        key = (round(lat, 2), round(lon, 2))
        w = weather_map.get(key, {})
        wind_speed_kmh = float(w.get("wind_speed_kmh", 0.0))
        humidity_pct = float(w.get("humidity_pct", 0.0))
        temp_c = float(w.get("temp_c", 0.0))

        # Environmental features
        e = env_map.get(key, {})
        soil_moisture = float(e.get("soil_moisture", 0.0))
        vpd_kpa = float(e.get("vpd_kpa", 0.0))
        et0_mm = float(e.get("et0_mm", 0.0))

        features.append(
            [
                bright_ti4,
                bright_ti5,
                frp,
                hour,
                month,
                lat_bin,
                lon_bin,
                wind_speed_kmh,
                humidity_pct,
                temp_c,
                soil_moisture,
                vpd_kpa,
                et0_mm,
            ]
        )

    X = np.array(features, dtype=float)  # noqa: N806 — X is standard ML notation for feature matrix
    probs = model.predict_proba(X)[:, 1]
    return [round(float(p), 4) for p in probs]


# ---------------------------------------------------------------------------
# Helper: load weather + environmental lookups from DB
# ---------------------------------------------------------------------------


def _build_weather_map(con: duckdb.DuckDBPyConnection) -> dict:
    """Build a lat/lon → weather dict from weather_observations table."""
    try:
        rows = con.execute(
            """
            SELECT
                ROUND(latitude, 2),
                ROUND(longitude, 2),
                wind_speed_kmh,
                humidity_pct,
                temp_c
            FROM weather_observations
            """
        ).fetchall()
        return {
            (r[0], r[1]): {
                "wind_speed_kmh": r[2],
                "humidity_pct": r[3],
                "temp_c": r[4],
            }
            for r in rows
        }
    except duckdb.CatalogException:
        return {}


def _build_env_map(con: duckdb.DuckDBPyConnection) -> dict:
    """Build a lat/lon → environmental dict from environmental_conditions table."""
    try:
        rows = con.execute(
            """
            SELECT
                ROUND(latitude, 2),
                ROUND(longitude, 2),
                soil_moisture,
                vpd_kpa,
                et0_mm
            FROM environmental_conditions
            """
        ).fetchall()
        return {
            (r[0], r[1]): {
                "soil_moisture": r[2],
                "vpd_kpa": r[3],
                "et0_mm": r[4],
            }
            for r in rows
        }
    except duckdb.CatalogException:
        return {}


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------


@app.get("/")
def root():
    return {"message": "AI Wildfire Tracker API is running"}


@app.get("/health")
def health():
    db_exists = os.path.exists(DB_PATH)
    model_loaded = _model is not None
    logger.info("Health check. db_exists=%s model_loaded=%s", db_exists, model_loaded)
    return {
        "status": "ok",
        "database_exists": db_exists,
        "db_path": DB_PATH,
        "model_loaded": model_loaded,
        "model_path": str(MODEL_PATH),
    }


@app.get("/fires")
def get_fires(
    confidence: str | None = Query(default=None, description="Filter by confidence"),
    region: str | None = Query(default=None, description="Region filter, e.g. 'ca'"),
):
    logger.info("GET /fires requested with confidence=%s region=%s", confidence, region)

    valid_regions = ["ca", "us", None]
    if region is not None and region.lower() not in valid_regions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid region '{region}'. Must be one of: ca, us",
        )

    valid_confidences = ["high", "nominal", "low"]
    if confidence is not None and confidence.lower() not in valid_confidences:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid confidence '{confidence}'. Must be one of: high, nominal, low",
        )

    if not os.path.exists(DB_PATH):
        logger.warning("Database file does not exist: %s", DB_PATH)
        return []

    con = duckdb.connect(DB_PATH)
    try:
        # Fetch fire rows — now includes bright_ti5 and acq_time for RF features
        query = """
            SELECT
                latitude, longitude,
                bright_ti4, bright_ti5, frp,
                confidence, acq_date, acq_time
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

        query += " ORDER BY acq_date DESC, acq_time DESC LIMIT 1000"

        rows = con.execute(query, params).fetchall()
        logger.info("Fetched %d fire rows", len(rows))

        # Load weather + environmental lookups for RF feature building
        weather_map = _build_weather_map(con)
        env_map = _build_env_map(con)

    except duckdb.CatalogException:
        logger.warning("Table 'fires' does not exist yet")
        return []
    except Exception:
        logger.exception("Unexpected error while reading fires")
        raise
    finally:
        con.close()

    # Compute RF risk scores for all rows in one batch
    risk_scores = compute_risk_batch(rows, weather_map, env_map)

    return [
        {
            "lat": r[0],
            "lon": r[1],
            "brightness": r[2],
            "frp": r[4],
            "confidence": r[5],
            "acq_date": r[6],
            "acq_time": r[7],
            "risk": risk_scores[i],
        }
        for i, r in enumerate(rows)
    ]
