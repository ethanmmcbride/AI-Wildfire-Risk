#python -m ai_wildfire.train --limit 500
import click
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from .data_loader import load_firms_table
from .features import build_feature_matrix
from .utils import set_seed, evaluate_model
from .model_store import save_model
from .configs import RANDOM_SEED

@click.command()
@click.option("--limit", default=None, help="Limit rows to load (for quick dev)")
@click.option("--test-size", default=0.2, show_default=True)
def train(limit, test_size):
    set_seed()
    print("Loading data from DB...")
    df = load_firms_table(limit=limit)
    print(f"Loaded {len(df)} rows")
    X, y = build_feature_matrix(df)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=RANDOM_SEED)
    model = LogisticRegression(max_iter=200)
    model.fit(X_train, y_train)
    metrics = evaluate_model(model, X_test, y_test)
    print("Evaluation:", metrics)
    meta = {"n_rows": len(df), "test_size": test_size, "model": "LogisticRegression"}
    save_path = save_model(model, meta)
    print("Model saved to", save_path)
    # persist metrics for CI artifact inspection
    import json, os
    from pathlib import Path
    artifact_dir = os.path.join(Path(__file__).resolve().parents[2], "artifacts")
    os.makedirs(artifact_dir, exist_ok=True)
    with open(os.path.join(artifact_dir, "metrics.json"), "w") as f:
        json.dump({"metrics": metrics}, f, indent=2)

if __name__ == "__main__":
    train()