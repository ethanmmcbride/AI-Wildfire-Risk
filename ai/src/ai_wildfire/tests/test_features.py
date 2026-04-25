import pandas as pd
from ai_wildfire.features import confidence_to_bin, build_feature_matrix

EXPECTED_FEATURE_COLUMNS = [
    "bright_ti4",
    "bright_ti5",
    "frp",
    "hour",
    "lat_bin",
    "lon_bin",
    "wind_speed_kmh",
    "humidity_pct",
    "temp_c",
]


def test_confidence_to_bin_handles_firms_and_noaa():
    s = pd.Series(["n", "h", "medium", "high", "low", "unknown"])
    out = confidence_to_bin(s).tolist()
    assert out == [0, 1, 0, 1, 0, 0]


def test_build_feature_matrix_returns_expected_columns():
    df = pd.DataFrame(
        [
            {
                "latitude": 34.1,
                "longitude": -118.2,
                "bright_ti4": 320.0,
                "bright_ti5": 290.0,
                "frp": 15.5,
                "acq_date": "2026-03-01",
                "acq_time": "1230",
                "confidence": "h",
            }
        ]
    )
    X, y = build_feature_matrix(df)
    assert list(X.columns) == EXPECTED_FEATURE_COLUMNS
    assert y.tolist() == [1]


def test_build_feature_matrix_fills_missing_weather_with_zero():
    df = pd.DataFrame(
        [
            {
                "latitude": 34.1,
                "longitude": -118.2,
                "bright_ti4": 320.0,
                "bright_ti5": 290.0,
                "frp": 15.5,
                "acq_date": "2026-03-01",
                "acq_time": "1230",
                "confidence": "h",
            }
        ]
    )
    X, _ = build_feature_matrix(df)
    assert X.iloc[0]["wind_speed_kmh"] == 0.0
    assert X.iloc[0]["humidity_pct"] == 0.0
    assert X.iloc[0]["temp_c"] == 0.0


def test_build_feature_matrix_preserves_weather_values():
    df = pd.DataFrame(
        [
            {
                "latitude": 34.1,
                "longitude": -118.2,
                "bright_ti4": 320.0,
                "bright_ti5": 290.0,
                "frp": 15.5,
                "acq_date": "2026-03-01",
                "acq_time": "1230",
                "confidence": "h",
                "wind_speed_kmh": 25.0,
                "humidity_pct": 15.0,
                "temp_c": 38.0,
            }
        ]
    )
    X, _ = build_feature_matrix(df)
    assert X.iloc[0]["wind_speed_kmh"] == 25.0
    assert X.iloc[0]["humidity_pct"] == 15.0
    assert X.iloc[0]["temp_c"] == 38.0
