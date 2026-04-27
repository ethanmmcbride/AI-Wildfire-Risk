import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

import duckdb
import joblib
import pandas as pd
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

# ---------------------------------------------------------------------------
# Operational metrics — module-level, reset on process restart
# ---------------------------------------------------------------------------
_PROCESS_START = time.time()
_request_counts: dict[str, int] = {"fires": 0, "health": 0, "metrics": 0}
_last_fires_response_ms: float | None = None
_last_health_response_ms: float | None = None

# Model path — defaults to ai/artifacts relative to project root.
# Override with MODEL_PATH env var for different environments.
_DEFAULT_MODEL_PATH = (
    Path(__file__).parent.parent.parent.parent.parent / "ai" / "artifacts" / "baseline_model.joblib"
)
MODEL_PATH = Path(os.getenv("MODEL_PATH", str(_DEFAULT_MODEL_PATH)))

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}

REGION_BOUNDS = {
    "us": {"min_lat": 24.0, "max_lat": 49.5, "min_lon": -125.0, "max_lon": -66.5},
    "ca": {"min_lat": 32.5, "max_lat": 42.1, "min_lon": -124.5, "max_lon": -114.0},
    "fl": {"min_lat": 24.5, "max_lat": 31.0, "min_lon": -87.6, "max_lon": -80.0},
    "tx": {"min_lat": 25.8, "max_lat": 36.5, "min_lon": -106.6, "max_lon": -93.5},
    "or": {"min_lat": 42.0, "max_lat": 46.3, "min_lon": -124.6, "max_lon": -116.5},
    "wa": {"min_lat": 45.5, "max_lat": 49.0, "min_lon": -124.8, "max_lon": -116.9},
    "az": {"min_lat": 31.3, "max_lat": 37.0, "min_lon": -114.8, "max_lon": -109.0},
    "co": {"min_lat": 37.0, "max_lat": 41.0, "min_lon": -109.1, "max_lon": -102.0},
    "ga": {"min_lat": 30.4, "max_lat": 35.0, "min_lon": -85.6, "max_lon": -80.8},
}

US_BOUNDS = REGION_BOUNDS["us"]
CA_BOUNDS = REGION_BOUNDS["ca"]

# ---------------------------------------------------------------------------
# Model loading — loaded once at startup, not on every request
# ---------------------------------------------------------------------------

_model = None
_model_status = "not_loaded"
_model_error: str | None = None


class ModelUnavailableError(RuntimeError):
    """Raised when RF scoring is required but the model cannot be loaded."""


def _env_bool(name: str) -> bool | None:
    value = os.getenv(name)
    if value is None:
        return None

    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False

    raise ValueError(f"{name} must be one of: true, false, 1, 0, yes, no, on, off")


def _model_path_configured() -> bool:
    return "MODEL_PATH" in os.environ


def _fallback_enabled() -> bool:
    configured = _env_bool("ALLOW_MODEL_FALLBACK")
    if configured is not None:
        return configured

    # Local/dev defaults can run without an artifact, but an explicit MODEL_PATH
    # means the caller expects RF inference and should not silently fall back.
    return not _model_path_configured()


def _mark_model_status(status: str, error: str | None = None) -> None:
    global _model_status, _model_error
    _model_status = status
    _model_error = error


def _load_model():
    """
    Load the trained Random Forest model from disk.
    Called once at startup. Returns None only when fallback mode is allowed.
    """
    global _model
    if _model is not None:
        _mark_model_status("loaded")
        return _model

    if not MODEL_PATH.exists():
        message = f"RF model not found at {MODEL_PATH}"
        if _fallback_enabled():
            _mark_model_status("fallback", message)
            logger.warning("%s — using brightness formula fallback", message)
            return None

        _mark_model_status("unavailable", message)
        logger.error("%s and fallback is disabled", message)
        raise ModelUnavailableError(message)

    try:
        _model = joblib.load(MODEL_PATH)
        _mark_model_status("loaded")
        logger.info("RF model loaded from %s", MODEL_PATH)
        return _model
    except Exception as exc:
        message = f"Failed to load RF model from {MODEL_PATH}: {exc}"
        if _fallback_enabled():
            _mark_model_status("fallback", message)
            logger.error("%s — using brightness formula fallback", message)
            return None

        _mark_model_status("unavailable", message)
        logger.error("%s", message)
        raise ModelUnavailableError(message) from exc


def _health_status(model_loaded: bool) -> str:
    if model_loaded:
        return "ok"
    if _fallback_enabled() and _model_status == "fallback":
        return "degraded"
    if _model_status == "unavailable":
        return "error"
    return "unknown"


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
    if not rows:
        return []

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
            {
                "bright_ti4": bright_ti4,
                "bright_ti5": bright_ti5,
                "frp": frp,
                "hour": hour,
                "month": month,
                "lat_bin": lat_bin,
                "lon_bin": lon_bin,
                "wind_speed_kmh": wind_speed_kmh,
                "humidity_pct": humidity_pct,
                "temp_c": temp_c,
                "soil_moisture": soil_moisture,
                "vpd_kpa": vpd_kpa,
                "et0_mm": et0_mm,
            }
        )

    X = pd.DataFrame(features, columns=_FEATURE_ORDER)  # noqa: N806
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
    global _last_health_response_ms
    _t0 = time.perf_counter()
    _request_counts["health"] += 1
    db_exists = os.path.exists(DB_PATH)
    try:
        model_loaded = _load_model() is not None
    except ModelUnavailableError:
        model_loaded = False

    logger.info(
        "Health check. db_exists=%s model_loaded=%s model_status=%s",
        db_exists,
        model_loaded,
        _model_status,
    )
    result = {
        "status": _health_status(model_loaded),
        "database_exists": db_exists,
        "db_path": DB_PATH,
        "model_loaded": model_loaded,
        "model_path": str(MODEL_PATH),
        "model_status": _model_status,
        "fallback_enabled": _fallback_enabled(),
    }
    _last_health_response_ms = round((time.perf_counter() - _t0) * 1000, 2)
    return result


@app.get("/metrics")
def get_metrics():
    _request_counts["metrics"] += 1
    return {
        "uptime_seconds": round(time.time() - _PROCESS_START, 1),
        "request_counts": dict(_request_counts),
        "last_fires_response_ms": _last_fires_response_ms,
        "last_health_response_ms": _last_health_response_ms,
    }


@app.get("/fires")
def get_fires(
    confidence: str | None = Query(default=None, description="Filter by confidence"),
    region: str | None = Query(default=None, description="Region filter, e.g. 'ca'"),
):
    global _last_fires_response_ms
    _t0 = time.perf_counter()
    _request_counts["fires"] += 1
    try:
        logger.info("GET /fires requested with confidence=%s region=%s", confidence, region)

        valid_regions = list(REGION_BOUNDS.keys())
        if region is not None and region.lower() not in valid_regions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid region '{region}'. Must be one of: {', '.join(valid_regions)}",
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

            if region and region.lower() != "us":
                bounds = REGION_BOUNDS.get(region.lower())
                if bounds:
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

            query += " ORDER BY acq_date DESC, acq_time DESC LIMIT 1000"

            rows = con.execute(query, params).fetchall()
            logger.info("Fetched %d fire rows", len(rows))

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
    except ModelUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail="RF model is unavailable and fallback is disabled",
        ) from exc
    finally:
        _last_fires_response_ms = round((time.perf_counter() - _t0) * 1000, 2)
