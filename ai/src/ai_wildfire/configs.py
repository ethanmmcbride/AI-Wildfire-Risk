import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

env_db_path = os.getenv("DB_PATH")
if env_db_path:
    db_path = Path(env_db_path)
    if not db_path.is_absolute():
        db_path = REPO_ROOT / db_path
    DB_PATH = str(db_path)
else:
    DB_PATH = str(REPO_ROOT / "wildfire.db")

ARTIFACT_DIR = REPO_ROOT / "ai" / "artifacts"
MODEL_FILENAME = "baseline_model.joblib"
METRICS_FILENAME = "metrics.json"
RANDOM_SEED = 42
MODEL_CLASS_WEIGHT = "balanced"
