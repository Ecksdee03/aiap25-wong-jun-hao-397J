"""Data ingestion: fetch the SQLite database and load the bookings table."""

import logging
import sqlite3
import urllib.request
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def ensure_database(db_path: str, db_url: str) -> Path:
    """Return the path to the SQLite DB, downloading it first if absent.

    The DB is not committed to the repository, so a fresh clone (e.g. the
    GitHub Actions runner) fetches it on first run.
    """
    path = Path(db_path)
    if not path.exists():
        logger.info("Database not found at %s - downloading from source", path)
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(db_url, path)
        logger.info("Downloaded %s (%.1f MB)", path, path.stat().st_size / 1e6)
    return path


def load_bookings(db_path: str, table: str = "bookings") -> pd.DataFrame:
    """Load the bookings table via SQLite into a DataFrame."""
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql(f"SELECT * FROM {table}", conn)
    logger.info("Loaded %d rows x %d columns from table '%s'", *df.shape, table)
    return df
