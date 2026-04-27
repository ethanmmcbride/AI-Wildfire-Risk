from ai_wildfire import model_store
from ai_wildfire.features import build_feature_matrix


def _run_predict(golden_df):
    """Reproduce the predict_from_db logic against the golden dataset directly."""
    X, _ = build_feature_matrix(golden_df)
    model = model_store.load_model()

    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)[:, 1]
    else:
        probs = model.predict(X)

    df_out = golden_df.copy()
    df_out["pred_score"] = probs
    df_out = df_out.sort_values("pred_score", ascending=False)
    return df_out


def test_high_confidence_detections_score_above_threshold():
    """
    After model training, high-confidence detections must score >= 0.5.
    Verifies the RF model has not regressed on its primary use case.
    """
    from ai_wildfire.predict import predict_from_db
    from unittest.mock import patch
    import duckdb
    import tempfile
    import os

    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    os.unlink(db_path)
    con = duckdb.connect(db_path)
    con.execute("""
        CREATE TABLE fires (
            latitude DOUBLE, longitude DOUBLE,
            bright_ti4 DOUBLE, bright_ti5 DOUBLE,
            frp DOUBLE, acq_date VARCHAR,
            acq_time VARCHAR, confidence VARCHAR
        )
    """)
    con.execute("""
        INSERT INTO fires VALUES
            (34.05, -118.25, 367.0, 320.0, 55.0, '2024-08-01', '1200', 'h'),
            (36.77, -119.42, 367.0, 315.0, 40.0, '2024-08-01', '1300', 'h'),
            (37.88, -122.27, 367.0, 310.0, 35.0, '2024-08-01', '1400', 'h')
    """)
    con.close()

    try:
        with patch("ai_wildfire.configs.DB_PATH", db_path):
            result = predict_from_db(limit=10)
        high_conf = result[result["confidence"] == "h"]
        assert len(high_conf) > 0
        median_score = high_conf["pred_score"].median()
        assert median_score >= 0.5, (
            f"REG-3 FAILED: median risk score for h-confidence = {median_score}"
        )
    finally:
        os.unlink(db_path)


def test_predict_returns_dataframe_with_scores(golden_df, trained_model_path):
    df_out = _run_predict(golden_df)
    assert "pred_score" in df_out.columns


def test_predict_scores_are_probabilities(golden_df, trained_model_path):
    df_out = _run_predict(golden_df)
    assert (df_out["pred_score"] >= 0.0).all(), "All scores must be >= 0.0"
    assert (df_out["pred_score"] <= 1.0).all(), "All scores must be <= 1.0"


def test_predict_output_sorted_descending(golden_df, trained_model_path):
    df_out = _run_predict(golden_df)
    scores = df_out["pred_score"].tolist()
    assert scores == sorted(scores, reverse=True), (
        "Output must be sorted by pred_score descending"
    )


def test_predict_output_shape(golden_df, trained_model_path):
    df_out = _run_predict(golden_df)
    assert len(df_out) == len(golden_df)
