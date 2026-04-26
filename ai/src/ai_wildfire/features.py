"""
features.py — Feature engineering for AI Wildfire Risk ML pipeline
ai/src/ai_wildfire/features.py

Builds the feature matrix used by the Random Forest classifier.
Joins fires table with weather_observations and environmental_conditions
from wildfire.db to create a rich feature set for risk scoring.

Label definition:
    1 = high-confidence satellite fire detection (confidence = 'h' or 'high')
    0 = nominal or low confidence detection

Feature groups:
    Satellite:      bright_ti4, bright_ti5, frp
    Temporal:       hour, month
    Spatial:        lat_bin, lon_bin
    Weather (NWS):  wind_speed_kmh, humidity_pct, temp_c
    Environmental:  soil_moisture, vpd_kpa, et0_mm
"""

import pandas as pd


# ---------------------------------------------------------------------------
# Label encoding
# ---------------------------------------------------------------------------


def confidence_to_bin(conf_series: pd.Series) -> pd.Series:
    """
    Convert satellite confidence values to binary label.

    Label = 1 (high-confidence fire detection):
        FIRMS SP/NRT: 'h'
        Text labels:  'high'

    Label = 0 (nominal / low confidence):
        FIRMS SP/NRT: 'n' (nominal), 'l' (low)
        Text labels:  'nominal', 'medium', 'low'
        Unknown:      default 0

    This label represents satellite-confirmed fire detection confidence,
    used as the ground-truth target for the Random Forest classifier.
    The model learns to predict which environmental + satellite conditions
    correlate with high-confidence fire events.
    """
    s = conf_series.astype(str).str.strip().str.lower()

    text_map = {
        "h": 1,
        "high": 1,
        "n": 0,
        "nominal": 0,
        "l": 0,
        "low": 0,
        "medium": 0,
    }

    return s.map(text_map).fillna(0).astype(int)


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------


def basic_preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """Add label, temporal, and spatial features to a fires DataFrame."""
    df = df.copy()

    df["confidence_bin"] = confidence_to_bin(df["confidence"])

    df["acq_datetime"] = pd.to_datetime(
        df["acq_date"].astype(str) + " " + df["acq_time"].astype(str).str.zfill(4),
        format="%Y-%m-%d %H%M",
        errors="coerce",
    )
    df["hour"] = df["acq_datetime"].dt.hour.fillna(0).astype(int)
    df["month"] = df["acq_datetime"].dt.month.fillna(0).astype(int)

    df["lat_bin"] = (df["latitude"].astype(float) // 1).astype(int)
    df["lon_bin"] = (df["longitude"].astype(float) // 1).astype(int)

    return df


# ---------------------------------------------------------------------------
# Weather + environmental join
# ---------------------------------------------------------------------------


def join_weather(fires_df: pd.DataFrame, weather_df: pd.DataFrame) -> pd.DataFrame:
    """
    Left-join weather observations to fire detections on rounded lat/lon.
    Unmatched rows get 0.0 for all weather features.
    """
    if weather_df.empty:
        fires_df["wind_speed_kmh"] = 0.0
        fires_df["humidity_pct"] = 0.0
        fires_df["temp_c"] = 0.0
        return fires_df

    weather_df = weather_df.copy()
    weather_df["lat_r"] = weather_df["latitude"].round(2)
    weather_df["lon_r"] = weather_df["longitude"].round(2)
    weather_df = weather_df[
        ["lat_r", "lon_r", "wind_speed_kmh", "humidity_pct", "temp_c"]
    ].drop_duplicates(subset=["lat_r", "lon_r"])

    fires_df["lat_r"] = fires_df["latitude"].round(2)
    fires_df["lon_r"] = fires_df["longitude"].round(2)

    merged = fires_df.merge(weather_df, on=["lat_r", "lon_r"], how="left")
    merged["wind_speed_kmh"] = merged["wind_speed_kmh"].fillna(0.0)
    merged["humidity_pct"] = merged["humidity_pct"].fillna(0.0)
    merged["temp_c"] = merged["temp_c"].fillna(0.0)
    merged = merged.drop(columns=["lat_r", "lon_r"])
    return merged


def join_environmental(fires_df: pd.DataFrame, env_df: pd.DataFrame) -> pd.DataFrame:
    """
    Left-join environmental conditions to fire detections on rounded lat/lon.
    Unmatched rows get 0.0 for all environmental features.
    """
    if env_df.empty:
        fires_df["soil_moisture"] = 0.0
        fires_df["vpd_kpa"] = 0.0
        fires_df["et0_mm"] = 0.0
        return fires_df

    env_df = env_df.copy()
    env_df["lat_r"] = env_df["latitude"].round(2)
    env_df["lon_r"] = env_df["longitude"].round(2)
    env_df = env_df[
        ["lat_r", "lon_r", "soil_moisture", "vpd_kpa", "et0_mm"]
    ].drop_duplicates(subset=["lat_r", "lon_r"])

    fires_df["lat_r"] = fires_df["latitude"].round(2)
    fires_df["lon_r"] = fires_df["longitude"].round(2)

    merged = fires_df.merge(env_df, on=["lat_r", "lon_r"], how="left")
    merged["soil_moisture"] = merged["soil_moisture"].fillna(0.0)
    merged["vpd_kpa"] = merged["vpd_kpa"].fillna(0.0)
    merged["et0_mm"] = merged["et0_mm"].fillna(0.0)
    merged = merged.drop(columns=["lat_r", "lon_r"])
    return merged


# ---------------------------------------------------------------------------
# Public feature matrix builder
# ---------------------------------------------------------------------------

FEATURE_COLS = [
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


def build_feature_matrix(
    fires_df: pd.DataFrame,
    weather_df: pd.DataFrame | None = None,
    env_df: pd.DataFrame | None = None,
):
    """
    Build the full feature matrix for Random Forest training or inference.

    Args:
        fires_df:   DataFrame from fires table (required)
        weather_df: DataFrame from weather_observations table (optional)
        env_df:     DataFrame from environmental_conditions table (optional)

    Returns:
        X: DataFrame of features (FEATURE_COLS)
        y: Series of binary labels (confidence_bin)
    """
    df = basic_preprocess(fires_df)

    if weather_df is not None and not weather_df.empty:
        df = join_weather(df, weather_df)
    else:
        df["wind_speed_kmh"] = 0.0
        df["humidity_pct"] = 0.0
        df["temp_c"] = 0.0

    if env_df is not None and not env_df.empty:
        df = join_environmental(df, env_df)
    else:
        df["soil_moisture"] = 0.0
        df["vpd_kpa"] = 0.0
        df["et0_mm"] = 0.0

    X = df[FEATURE_COLS].fillna(0)
    y = df["confidence_bin"]
    return X, y
