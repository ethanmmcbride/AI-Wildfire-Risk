import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from ai_wildfire import model_store
from ai_wildfire.configs import MODEL_FILENAME, RANDOM_SEED
from ai_wildfire.features import build_feature_matrix
from ai_wildfire.utils import evaluate_model, set_seed


def _train_on_golden(golden_df, test_size=0.2):
    set_seed()
    X, y = build_feature_matrix(golden_df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=RANDOM_SEED
    )
    model = LogisticRegression(max_iter=200)
    model.fit(X_train, y_train)
    return model, X_test, y_test


def test_train_produces_model_artifact(golden_df, tmp_artifact_dir):
    model, _, _ = _train_on_golden(golden_df)
    path = model_store.save_model(
        model, {"model": "LogisticRegression", "n_rows": len(golden_df)}
    )
    assert Path(path).exists()
    assert Path(path).name == MODEL_FILENAME


def test_train_produces_metadata(golden_df, tmp_artifact_dir):
    model, _, _ = _train_on_golden(golden_df)
    model_store.save_model(
        model, {"model": "LogisticRegression", "n_rows": len(golden_df)}
    )

    meta_path = tmp_artifact_dir / (MODEL_FILENAME + ".metadata.json")
    assert meta_path.exists()

    with open(meta_path) as f:
        meta = json.load(f)

    assert "saved_at" in meta
    assert meta["model"] == "LogisticRegression"
    assert meta["n_rows"] == 50


def test_train_metrics_are_reasonable(golden_df, tmp_artifact_dir):
    model, X_test, y_test = _train_on_golden(golden_df)
    metrics = evaluate_model(model, X_test, y_test)

    assert isinstance(metrics["report"], dict)
    assert "accuracy" in metrics["report"]
    assert metrics["report"]["accuracy"] >= 0.5

    assert metrics["auc"] is not None
    assert isinstance(metrics["auc"], float)
    assert 0.0 <= metrics["auc"] <= 1.0


def test_train_deterministic(golden_df, tmp_artifact_dir):
    model_a, _, _ = _train_on_golden(golden_df)
    model_b, _, _ = _train_on_golden(golden_df)
    np.testing.assert_array_equal(model_a.coef_, model_b.coef_)
    np.testing.assert_array_equal(model_a.intercept_, model_b.intercept_)


def test_train_both_classes_in_split(golden_df):
    X, y = build_feature_matrix(golden_df)
    _, _, _, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_SEED)
    unique_classes = set(y_test.tolist())
    assert 0 in unique_classes, "Test split must contain class 0"
    assert 1 in unique_classes, "Test split must contain class 1"
