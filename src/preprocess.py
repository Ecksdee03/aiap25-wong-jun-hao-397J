"""Cleaning: fix the data-quality issues identified in the EDA.

Every rule here mirrors a documented finding in eda.ipynb:
- exact duplicate rows (353)
- target stored under six encodings (0/1, Yes/No, true/false)
- numeric columns stored as text ("30 days" in lead_time)
- categorical case/spacing/typo variants (" No  Deposit ", "Transiant", "Offline TA/T0")
- hidden missingness as empty strings (agent, company, promo_code)
- country as a mix of ISO codes, full names, and junk values
- impossible values e.g. 0-guest bookings, lead_time > 2 years etc
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

JUNK = {"", "-", "--", "unknown", "null", "na", "n/a", "none"}

TARGET_MAP = {"0": 0, "No": 0, "false": 0, "1": 1, "Yes": 1, "true": 1}

MEAL_MAP = {"bb": "BB", "hb": "HB", "fb": "FB", "sc": "SC", "undefined": "Undefined"}
DEPOSIT_MAP = {
    "no deposit": "No Deposit", "no depost": "No Deposit",
    "non refund": "Non Refund", "refundable": "Refundable",
}
CUSTOMER_MAP = {
    "transient": "Transient", "transiant": "Transient",
    "transient party": "Transient-Party", "contract": "Contract", "group": "Group",
}
SEGMENT_MAP = {
    "online ta": "Online TA", "offline ta/to": "Offline TA/TO",
    "offline ta/t0": "Offline TA/TO",  # zero-for-O typo seen in data
    "direct": "Direct", "groups": "Groups", "corporate": "Corporate",
    "complementary": "Complementary", "aviation": "Aviation", "undefined": "Undefined",
}
CHANNEL_MAP = {
    "ta/to": "TA/TO", "direct": "Direct", "corporate": "Corporate",
    "gds": "GDS", "undefined": "Undefined",
}
MONTH_MAP = {
    "Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April",
    "Jun": "June", "Jul": "July", "Aug": "August", "Sep": "September",
    "Oct": "October", "Nov": "November", "Dec": "December",
}
COUNTRY_MAP = {
    "Australia": "AUS", "Malaysia": "MYS", "Singapore": "SGP", "Indonesia": "IDN",
    "China": "CHN", "Other": "OTH", "India": "IND", "Japan": "JPN",
    "United States": "USA", "Hong Kong": "HKG", "United Kingdom": "GBR",
    "Thailand": "THA", "South Korea": "KOR", "Philippines": "PHL",
    "Myanmar": "MMR", "Taiwan": "TWN", "Vietnam": "VNM", "New Zealand": "NZL",
}

NUMERIC_COLS = [
    "arrival_date_year", "arrival_date_day_of_month", "stays_in_weekend_nights",
    "stays_in_week_nights", "adults", "children", "babies", "is_repeated_guest",
    "previous_cancellations", "previous_bookings_not_canceled", "booking_changes",
    "days_in_waiting_list", "adr", "required_car_parking_spaces",
    "total_of_special_requests",
]

# Unusable or replaced columns (rationale in eda.ipynb / README)
DROP_COLS = [
    "Unnamed: 0",               # leftover export index
    "booking_id",               # identifier; only needed for duplicate detection
    "arrival_date_week_number", # ~490 corrupt values; redundant with month + day
    "reservation_status_date",  # only set when outcome recorded -> leakage
    "agent",                    # high-cardinality ID -> replaced by has_agent
    "company",                  # high-cardinality ID -> replaced by has_company
]


def _normalise_categorical(series: pd.Series, mapping: dict, junk_to=np.nan) -> pd.Series:
    """Collapse case/space/hyphen variants to a key, then map to canonical values."""
    key = (
        series.astype(str)
        .str.strip()
        .str.replace(r"[\s\-]+", " ", regex=True)
        .str.lower()
    )
    out = key.map(mapping)
    out[key.isin(JUNK)] = junk_to
    return out


def clean_bookings(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Apply all cleaning rules; returns a modelling-ready DataFrame."""
    n0 = len(df)
    df = df.drop(columns=[c for c in ("Unnamed: 0",) if c in df.columns])
    df = df.drop_duplicates()
    logger.info("Dropped %d exact duplicate rows", n0 - len(df))

    # Target: six observed encodings -> {0, 1}
    df["is_canceled"] = df["is_canceled"].astype(str).str.strip().map(TARGET_MAP)
    if df["is_canceled"].isna().any():
        bad = df["is_canceled"].isna().sum()
        logger.warning("Dropping %d rows with unmappable target values", bad)
        df = df.dropna(subset=["is_canceled"])
    df["is_canceled"] = df["is_canceled"].astype(int)

    # Categorical normalisation
    df["meal"] = _normalise_categorical(df["meal"], MEAL_MAP, junk_to="Undefined")
    df["deposit_type"] = _normalise_categorical(df["deposit_type"], DEPOSIT_MAP)
    df["customer_type"] = _normalise_categorical(df["customer_type"], CUSTOMER_MAP)
    df["market_segment"] = _normalise_categorical(df["market_segment"], SEGMENT_MAP)
    df["distribution_channel"] = _normalise_categorical(df["distribution_channel"], CHANNEL_MAP)
    df["arrival_date_month"] = df["arrival_date_month"].astype(str).str.strip().replace(MONTH_MAP)

    # lead_time contains text like "30 days" -> extract digits
    df["lead_time"] = pd.to_numeric(
        df["lead_time"].astype(str).str.extract(r"(\d+)")[0], errors="coerce"
    )

    # country: word forms -> ISO, junk -> OTH
    c = df["country"].astype(str).str.strip().replace(COUNTRY_MAP)
    c[c.str.lower().isin(JUNK)] = np.nan
    df["country"] = c.fillna("OTH")

    # numerics stored as text
    present = [c for c in NUMERIC_COLS if c in df.columns]
    df[present] = df[present].apply(pd.to_numeric, errors="coerce")

    # hidden missingness: blank strings -> NaN; agent/company -> presence flags
    df = df.replace("", np.nan)
    df["has_agent"] = df["agent"].notna().astype(int) if "agent" in df else 0
    df["has_company"] = df["company"].notna().astype(int) if "company" in df else 0
    df["promo_code"] = df["promo_code"].fillna("NONE")

    # unmapped categorical junk -> explicit "Unknown" level (no rows fabricated or lost)
    for col in ["meal", "deposit_type", "customer_type", "market_segment",
                "distribution_channel"]:
        df[col] = df[col].fillna("Unknown")

    df = df.drop(columns=[c for c in DROP_COLS if c in df.columns])

    # Impossible-value rows (rules validated in eda.ipynb; thresholds in config).
    # Extreme-but-plausible values (high ADR, large parties) are deliberately kept.
    cl = cfg["cleaning"]
    guests = df["adults"] + df["children"] + df["babies"]
    nights = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
    mask = df["lead_time"] > cl["max_lead_time"]
    if cl.get("drop_negative_adr", True):
        mask |= df["adr"] < 0
    if cl.get("drop_zero_guest_bookings", True):
        mask |= guests == 0
    if cl.get("drop_zero_night_stays", True):
        mask |= nights == 0
    mask = mask.fillna(False)
    logger.info("Dropped %d rows with impossible values (%.2f%%)",
                mask.sum(), 100 * mask.mean())
    df = df.loc[~mask].copy()

    logger.info("Clean dataset: %d rows x %d columns", *df.shape)
    return df
