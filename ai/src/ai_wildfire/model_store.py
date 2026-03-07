import os, joblib, json
from datetime import datetime
from .configs import ARTIFACT_DIR, MODEL_FILENAME

os.makedirs(ARTIFACT_DIR, exist_ok=True)

def save_model(model, metadata: dict):
    path = os.path.join(ARTIFACT_DIR, MODEL_FILENAME)
    joblib.dump(model, path)
    meta_path = os.path.join(ARTIFACT_DIR, MODEL_FILENAME + ".metadata.json")
    metadata.update({"saved_at": datetime.utcnow().isoformat()})
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    return path

def load_model():
    path = os.path.join(ARTIFACT_DIR, MODEL_FILENAME)
    if not os.path.exists(path):
        raise FileNotFoundError("No model artifact found. Train first.")
    return joblib.load(path)