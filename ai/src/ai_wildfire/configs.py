import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

DB_PATH = os.getenv(
    "WILDFIRE_DB",
    str(REPO_ROOT / "wildfire.db")
)

ARTIFACT_DIR = REPO_ROOT / "ai" / "artifacts"
MODEL_FILENAME = "baseline_model.joblib"
RANDOM_SEED = 42