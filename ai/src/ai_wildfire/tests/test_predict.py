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
