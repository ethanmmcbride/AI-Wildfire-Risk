import numpy as np
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    roc_auc_score,
)

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

    report = classification_report(y_test, preds, output_dict=True, zero_division=0)

    auc = None
    pr_auc = None
    if probs is not None and len(set(y_test)) > 1:
        auc = roc_auc_score(y_test, probs)
        pr_auc = average_precision_score(y_test, probs)

    f1_class_1 = report.get("1", {}).get("f1-score", 0.0)

    return {"report": report, "auc": auc, "pr_auc": pr_auc, "f1_class_1": f1_class_1}
