"""Pipeline entry point.

Flow: load config -> fetch data (SQLite) -> clean -> derive features ->
time-based split -> fit preprocessing + model on train -> evaluate on test.

Run:  ./run.sh            (or: python -m src.main --config config.yaml)
"""

import argparse
import logging

import yaml
from sklearn.pipeline import Pipeline

from src.data_loader import ensure_database, load_bookings
from src.evaluate import evaluate
from src.features import add_derived_features, build_preprocessor, split_xy, time_split
from src.model import build_model
from src.preprocess import clean_bookings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Travelers' Inn cancellation prediction pipeline")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config")
    return parser.parse_args()


def main():
    args = parse_args()
    with open(args.config) as f:
        cfg = yaml.safe_load(f)
    logger.info("Config loaded from %s", args.config)

    # 1. Ingest
    db_path = ensure_database(cfg["data"]["db_path"], cfg["data"]["db_url"])
    raw = load_bookings(db_path, cfg["data"]["table"])

    # 2. Clean (rules derived from EDA findings)
    df = clean_bookings(raw, cfg)

    # 3. Features + time-based split (train: past years, test: most recent)
    df = add_derived_features(df)
    train_df, test_df = time_split(df, cfg)
    x_train, y_train = split_xy(train_df, cfg)
    x_test, y_test = split_xy(test_df, cfg)

    # 4. Fit: preprocessing is inside the Pipeline, so encoders/imputers/scalers
    #    are fitted on training data only (no test-set leakage).
    pipeline = Pipeline([
        ("preprocess", build_preprocessor(x_train, cfg)),
        ("model", build_model(cfg)),
    ])
    logger.info("Fitting on %d rows", len(x_train))
    pipeline.fit(x_train, y_train)

    # 5. Evaluate on the held-out future year
    evaluate(pipeline, x_test, y_test, cfg)
    logger.info("Pipeline complete.")


if __name__ == "__main__":
    main()
