import numpy as np
from sklearn.metrics import classification_report, roc_auc_score
from .configs import RANDOM_SEED


def set_seed(seed=RANDOM_SEED):
    import random

    random.seed(seed)
    np.random.seed(seed)


def evaluate_model(model, X_test, y_test):
    preds = model.predict(X_test)
    probs = None
    try:
        probs = model.predict_proba(X_test)[:, 1]
    except Exception:
        pass
    report = classification_report(y_test, preds, output_dict=True)
    auc = None
    if probs is not None:
        auc = roc_auc_score(y_test, probs)
    return {"report": report, "auc": auc}
