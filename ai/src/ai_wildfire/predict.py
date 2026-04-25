from .model_store import load_model
from .features import build_feature_matrix
from .data_loader import load_fires_with_weather


def predict_from_db(limit=10):
    df = load_fires_with_weather(limit=limit)

    X, _ = build_feature_matrix(df)
    model = load_model()
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)[:, 1]
    else:
        probs = model.predict(X)

    df_out = df.copy()
    df_out["pred_score"] = probs
    df_out = df_out.sort_values("pred_score", ascending=False)
    print(
        df_out[
            [
                "latitude",
                "longitude",
                "acq_date",
                "acq_time",
                "confidence",
                "pred_score",
            ]
        ].head(20)
    )

    return df_out
