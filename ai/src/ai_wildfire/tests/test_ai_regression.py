import numpy as np
import pandas as pd

from ai_wildfire.features import build_feature_matrix

FEATURE_COLUMNS = [
    "bright_ti4", "bright_ti5", "frp",
    "hour", "month", "lat_bin", "lon_bin",
    "wind_speed_kmh", "humidity_pct", "temp_c",
    "soil_moisture", "vpd_kpa", "et0_mm",
]

HIGH_CONFIDENCE_VALUES = {"high", "h"}


def test_feature_matrix_shape(golden_df):
    X, y = build_feature_matrix(golden_df)
    assert X.shape == (50, 13)
    assert len(y) == 50


def test_feature_matrix_columns(golden_df):
    X, _ = build_feature_matrix(golden_df)
    assert list(X.columns) == FEATURE_COLUMNS


def test_feature_matrix_no_nan(golden_df):
    X, _ = build_feature_matrix(golden_df)
    assert not X.isna().any().any(), "Feature matrix should have no NaN values"


def test_feature_matrix_dtypes(golden_df):
    X, _ = build_feature_matrix(golden_df)
    for col in X.columns:
        assert np.issubdtype(X[col].dtype, np.number), f"{col} should be numeric"


def test_labels_match_confidence_mapping(golden_df):
    _, y = build_feature_matrix(golden_df)
    expected = [
        1 if str(c).strip().lower() in HIGH_CONFIDENCE_VALUES else 0
        for c in golden_df["confidence"]
    ]
    assert y.tolist() == expected


def test_hour_extraction(golden_df):
    X, _ = build_feature_matrix(golden_df)
    df = golden_df.copy()
    df["_expected_hour"] = (
        pd.to_datetime(
            df["acq_date"].astype(str) + " " + df["acq_time"].astype(str).str.zfill(4),
            format="%Y-%m-%d %H%M",
            errors="coerce",
        )
        .dt.hour.fillna(0)
        .astype(int)
    )
    spot_checks = {
        "1210": 12,
        "0600": 6,
        "1430": 14,
        "1800": 18,
        "2100": 21,
        "0915": 9,
    }
    for acq_time_val, expected_hour in spot_checks.items():
        mask = golden_df["acq_time"].astype(str) == acq_time_val
        if mask.any():
            idx = mask.idxmax()
            assert X.iloc[idx]["hour"] == expected_hour, (
                f"acq_time={acq_time_val} should produce hour={expected_hour}"
            )


def test_spatial_bins(golden_df):
    X, _ = build_feature_matrix(golden_df)
    for idx, row in golden_df.iterrows():
        expected_lat_bin = int(float(row["latitude"]) // 1)
        expected_lon_bin = int(float(row["longitude"]) // 1)
        assert X.iloc[idx]["lat_bin"] == expected_lat_bin, (
            f"Row {idx}: lat {row['latitude']} should produce lat_bin={expected_lat_bin}"
        )
        assert X.iloc[idx]["lon_bin"] == expected_lon_bin, (
            f"Row {idx}: lon {row['longitude']} should produce lon_bin={expected_lon_bin}"
        )
