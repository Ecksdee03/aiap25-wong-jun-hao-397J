"""Model factory: instantiate the classifier named in the config."""

import logging

from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger(__name__)

MODELS = {
    "logistic_regression": LogisticRegression,
    "random_forest": RandomForestClassifier,
    "hist_gradient_boosting": HistGradientBoostingClassifier,
}


def build_model(cfg: dict):
    """Return an unfitted classifier configured from config.yaml.

    Swapping models is a one-line config change; each entry in MODELS has its
    own parameter block in the config file.
    """
    name = cfg["model"]["name"]
    if name not in MODELS:
        raise ValueError(f"Unknown model '{name}'. Choose one of: {sorted(MODELS)}")
    params = dict(cfg["model"].get(name, {}))
    # YAML null -> Python None is already handled by the YAML loader
    model = MODELS[name](**params)
    logger.info("Model: %s(%s)", name, params)
    return model
