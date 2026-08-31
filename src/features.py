"""Feature assembly: derived features, time-based split, and the sklearn
preprocessing transformer (fitted on training data only to avoid leakage)."""

import logging

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logger = logging.getLogger(__name__)

TARGET = "is_canceled"


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Simple engineered features motivated by the EDA."""
    df = df.copy()
    df["total_nights"] = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
    df["total_guests"] = df["adults"] + df["children"] + df["babies"]
    df["has_previous_cancellation"] = (df["previous_cancellations"] > 0).astype(int)
    return df


def time_split(df: pd.DataFrame, cfg: dict):
    """Train on earlier years, test on the most recent year.

    A random split would let the model train on bookings from the future of
    the ones it is tested on; splitting on arrival year simulates deployment.
    """
    sp = cfg["split"]
    year = df[sp["year_column"]].astype(int)
    train = df[year.isin(sp["train_years"])]
    test = df[year.isin(sp["test_years"])]
    logger.info("Split: %d train rows (%s), %d test rows (%s)",
                len(train), sp["train_years"], len(test), sp["test_years"])
    return train, test


def split_xy(df: pd.DataFrame, cfg: dict):
    """Separate features from target, dropping excluded columns."""
    exclude = set(cfg["features"]["exclude"]) | {TARGET}
    x = df.drop(columns=[c for c in exclude if c in df.columns])
    y = df[TARGET]
    return x, y


def build_preprocessor(x: pd.DataFrame, cfg: dict) -> ColumnTransformer:
    """One-hot encode categoricals (rare levels grouped), impute + scale numerics.

    Fitted downstream on the training split only, so imputation statistics,
    scaling parameters, and category vocabularies never see test data.
    """
    cat_cols = x.select_dtypes(include="object").columns.tolist()
    num_cols = x.select_dtypes(exclude="object").columns.tolist()
    logger.info("Features: %d categorical, %d numeric", len(cat_cols), len(num_cols))

    cat_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("onehot", OneHotEncoder(
            handle_unknown="infrequent_if_exist",
            min_frequency=cfg["features"]["rare_category_min_frequency"],
            sparse_output=False,
        )),
    ])
    num_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),  # no-op for trees, required for logistic regression
    ])
    return ColumnTransformer([
        ("cat", cat_pipe, cat_cols),
        ("num", num_pipe, num_cols),
    ])
