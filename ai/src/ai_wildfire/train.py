# python -m ai_wildfire.train --limit 500
"""
train.py — Random Forest model training for AI Wildfire Risk
ai/src/ai_wildfire/train.py

Trains a Random Forest classifier to score fire detection risk.
Uses all available data from wildfire.db:
    fires table              → satellite features + labels
    weather_observations     → NWS weather features (joined by lat/lon)
    environmental_conditions → Open-Meteo soil/VPD features (joined by lat/lon)

Outputs:
    ai/artifacts/baseline_model.joblib  — trained RF model
    ai/artifacts/metrics.json           — evaluation metrics + feature importances
"""

import json
import os

import click
import duckdb
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from .configs import ARTIFACT_DIR, DB_PATH, METRICS_FILENAME, RANDOM_SEED
from .features import FEATURE_COLS, build_feature_matrix
from .model_store import save_model
from .utils import set_seed


def load_all_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load fires, weather_observations, and environmental_conditions from DB.
    Returns empty DataFrames for tables that don't exist yet.
    """
    con = duckdb.connect(str(DB_PATH))

    fires_df = con.execute("SELECT * FROM fires").df()

    try:
        weather_df = con.execute("SELECT * FROM weather_observations").df()
    except Exception:
        weather_df = pd.DataFrame()

    try:
        env_df = con.execute("SELECT * FROM environmental_conditions").df()
    except Exception:
        env_df = pd.DataFrame()

    con.close()
    return fires_df, weather_df, env_df


@click.command()
@click.option("--limit", default=None, type=int, help="Limit fire rows (for quick dev)")
@click.option("--test-size", default=0.2, show_default=True)
@click.option("--n-estimators", default=100, show_default=True, help="RF trees")
def train(limit, test_size, n_estimators):
    set_seed()

    print("Loading data from DB...")
    fires_df, weather_df, env_df = load_all_tables()

    if limit:
        fires_df = fires_df.head(limit)

    print(f"Fires: {len(fires_df)} rows")
    print(f"Weather observations: {len(weather_df)} rows")
    print(f"Environmental conditions: {len(env_df)} rows")

    print("Building feature matrix...")
    X, y = build_feature_matrix(fires_df, weather_df, env_df)

    print(f"Feature matrix: {X.shape[0]} rows × {X.shape[1]} features")
    print(f"Label distribution: {y.value_counts().to_dict()}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=RANDOM_SEED, stratify=y
    )

    print(f"Training RandomForest (n_estimators={n_estimators}, class_weight=balanced)...")
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        class_weight="balanced",
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "model": "RandomForestClassifier",
        "n_estimators": n_estimators,
        "n_rows": len(fires_df),
        "n_features": len(FEATURE_COLS),
        "test_size": test_size,
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "auc_roc": round(roc_auc_score(y_test, y_proba), 4),
        "feature_importances": dict(
            zip(FEATURE_COLS, [round(float(i), 4) for i in model.feature_importances_])
        ),
    }

    print("\nEvaluation metrics:")
    for k, v in metrics.items():
        if k != "feature_importances":
            print(f"  {k}: {v}")

    print("\nFeature importances (ranked):")
    importances = sorted(
        metrics["feature_importances"].items(), key=lambda x: x[1], reverse=True
    )
    for feat, imp in importances:
        print(f"  {feat}: {imp:.4f}")

    print("\nClassification report:")
    print(classification_report(y_test, y_pred, target_names=["non-fire", "fire"]))

    # Save model
    meta = {
        "n_rows": len(fires_df),
        "test_size": test_size,
        "model": "RandomForestClassifier",
        "n_estimators": n_estimators,
        "features": FEATURE_COLS,
    }
    save_path = save_model(model, meta)
    print(f"Model saved to {save_path}")

    # Save metrics
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    with open(ARTIFACT_DIR / METRICS_FILENAME, "w") as f:
        json.dump({"metrics": metrics}, f, indent=2)
    print(f"Metrics saved to {ARTIFACT_DIR / METRICS_FILENAME}")


if __name__ == "__main__":
    train()
