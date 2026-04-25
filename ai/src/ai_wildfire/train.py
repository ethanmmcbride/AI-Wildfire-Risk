# python -m ai_wildfire.train --limit 500
import json
import os

import click
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from .configs import ARTIFACT_DIR, METRICS_FILENAME, MODEL_CLASS_WEIGHT, RANDOM_SEED
from .data_loader import load_fires_with_weather
from .features import build_feature_matrix
from .model_store import save_model
from .utils import evaluate_model, set_seed


@click.command()
@click.option("--limit", default=None, help="Limit rows to load (for quick dev)")
@click.option("--test-size", default=0.2, show_default=True)
def train(limit, test_size):
    set_seed()
    print("Loading data from DB...")
    df = load_fires_with_weather(limit=limit)
    print(f"Loaded {len(df)} rows")
    X, y = build_feature_matrix(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=RANDOM_SEED, stratify=y
    )
    model = LogisticRegression(max_iter=200, class_weight=MODEL_CLASS_WEIGHT)
    model.fit(X_train, y_train)
    metrics = evaluate_model(model, X_test, y_test)
    print("Evaluation:", metrics)
    meta = {
        "n_rows": len(df),
        "test_size": test_size,
        "model": "LogisticRegression",
        "class_weight": MODEL_CLASS_WEIGHT,
    }
    save_path = save_model(model, meta)
    print("Model saved to", save_path)
    os.makedirs(ARTIFACT_DIR, exist_ok=True)

    with open(ARTIFACT_DIR / METRICS_FILENAME, "w") as f:
        json.dump({"metrics": metrics}, f, indent=2)


if __name__ == "__main__":
    train()
