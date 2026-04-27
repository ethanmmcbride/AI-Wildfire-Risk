from pathlib import Path

import duckdb
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from ai_wildfire import configs, model_store
from ai_wildfire.features import build_feature_matrix
from ai_wildfire.utils import set_seed

FIXTURES_DIR = Path(__file__).parent / "fixtures"
GOLDEN_CSV = FIXTURES_DIR / "golden_fires.csv"


@pytest.fixture()
def golden_df():
    return pd.read_csv(GOLDEN_CSV)


@pytest.fixture()
def tmp_artifact_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(model_store, "ARTIFACT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def seeded_golden_db(tmp_path, monkeypatch, golden_df):
    db_path = str(tmp_path / "golden_test.db")
    con = duckdb.connect(db_path)
    con.execute("""
        CREATE TABLE fires (
            latitude DOUBLE,
            longitude DOUBLE,
            bright_ti4 DOUBLE,
            bright_ti5 DOUBLE,
            frp DOUBLE,
            acq_date VARCHAR,
            acq_time VARCHAR,
            confidence VARCHAR
        )
    """)
    con.execute("INSERT INTO fires SELECT * FROM golden_df")
    con.close()
    monkeypatch.setattr(configs, "DB_PATH", db_path)
    return db_path


@pytest.fixture()
def trained_model_path(golden_df, tmp_artifact_dir):
    set_seed()
    X, y = build_feature_matrix(golden_df)
    X_train, _, y_train, _ = train_test_split(
        X, y, test_size=0.2, random_state=configs.RANDOM_SEED, stratify=y
    )
    model = LogisticRegression(max_iter=200, class_weight=configs.MODEL_CLASS_WEIGHT)
    model.fit(X_train, y_train)
    path = model_store.save_model(
        model, {"model": "LogisticRegression", "n_rows": len(golden_df)}
    )
    return path
