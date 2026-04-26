import pandas as pd
from ai_wildfire.features import confidence_to_bin, build_feature_matrix


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
    assert list(X.columns) == [
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
    assert y.tolist() == [1]
