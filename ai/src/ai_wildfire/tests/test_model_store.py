from pathlib import Path
from sklearn.linear_model import LogisticRegression
from ai_wildfire import model_store


def test_save_and_load_model(tmp_path, monkeypatch):
    monkeypatch.setattr(model_store, "ARTIFACT_DIR", tmp_path)
    model = LogisticRegression()
    path = model_store.save_model(model, {"model": "LogisticRegression"})
    loaded = model_store.load_model()
    assert Path(path).exists()
    assert loaded.__class__.__name__ == "LogisticRegression"
