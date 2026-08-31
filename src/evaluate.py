"""Evaluation: metrics chosen for the business problem.

An unanticipated empty room (missed cancellation) costs more than an unnecessary
confirmation call (false alarm), so recall on the positive class is the primary
metric, reported alongside precision, F1, ROC-AUC and PR-AUC for a full picture.
The decision threshold is a config lever: lowering it trades precision for recall.
"""

import json
import logging
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

logger = logging.getLogger(__name__)


def evaluate(model, x_test, y_test, cfg: dict) -> dict:
    """Score the fitted model on the held-out (future-year) test set."""
    threshold = cfg["model"]["threshold"]
    proba = model.predict_proba(x_test)[:, 1]
    pred = (proba >= threshold).astype(int)

    metrics = {
        "model": cfg["model"]["name"],
        "threshold": threshold,
        "test_rows": int(len(y_test)),
        "test_positive_rate": round(float(np.mean(y_test)), 4),
        "recall_cancelled": round(float(recall_score(y_test, pred)), 4),
        "precision_cancelled": round(float(precision_score(y_test, pred)), 4),
        "f1_cancelled": round(float(f1_score(y_test, pred)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, proba)), 4),
        "pr_auc": round(float(average_precision_score(y_test, proba)), 4),
        "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
    }

    logger.info("Test metrics: %s", json.dumps(metrics, indent=2))
    print("\n" + classification_report(y_test, pred,
                                       target_names=["honoured", "cancelled/no-show"]))

    out_dir = Path(cfg["output"]["dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "metrics.json"
    out_path.write_text(json.dumps(metrics, indent=2))
    logger.info("Metrics written to %s", out_path)
    return metrics
