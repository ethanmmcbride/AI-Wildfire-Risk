import pandas as pd
import numpy as np

def confidence_to_bin(conf_series: pd.Series) -> pd.Series:
    """
    Convert FIRMS confidence values into a binary label.

    Your DB currently contains:
      - 'n' (nominal) -> 0
      - 'h' (high)    -> 1

    Also supports common text labels (low/nominal/high) just in case
    you ingest a different FIRMS product later.
    """
    s = conf_series.astype(str).str.strip().str.lower()

    text_map = {
        "n": 0,          # nominal (your dataset)
        "h": 1,          # high (your dataset)
        "low": 0,
        "nominal": 0,
        "high": 1,
        "l": 0,
    }

    return s.map(text_map).fillna(0).astype(int)

def basic_preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # label
    df["confidence_bin"] = confidence_to_bin(df["confidence"])

    # parse date/time -> hour of day
    # acq_time can be like "35" or "1230" so zfill to 4 digits
    df["acq_datetime"] = pd.to_datetime(
        df["acq_date"].astype(str) + " " + df["acq_time"].astype(str).str.zfill(4),
        format="%Y-%m-%d %H%M",
        errors="coerce",
    )
    df["hour"] = df["acq_datetime"].dt.hour.fillna(0).astype(int)

    # simple spatial bins (baseline feature)
    df["lat_bin"] = (df["latitude"].astype(float) // 1).astype(int)
    df["lon_bin"] = (df["longitude"].astype(float) // 1).astype(int)

    return df

def build_feature_matrix(df: pd.DataFrame):
    df = basic_preprocess(df)

    feature_cols = ["bright_ti4", "bright_ti5", "frp", "hour", "lat_bin", "lon_bin"]
    X = df[feature_cols].fillna(0)

    y = df["confidence_bin"]
    return X, y