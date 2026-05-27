"""
sellers_cleaning.py
-------------------
Cleans and validates the Olist sellers dataset.

Transformations applied
-----------------------
- Remove duplicate seller_id rows
- Normalise seller_state to uppercase 2-letter codes
- Standardise city names
- Cast datatypes

Usage
-----
    python -m src.transform.sellers_cleaning
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.utils.config import BRAZIL_STATE_CODES, PROCESSED_DIR, RAW_DIR
from src.utils.file_utils import ensure_directories, read_csv, save_csv
from src.utils.logging_utils import get_logger
from src.utils.validation_utils import (
    assert_no_duplicate_keys,
    assert_no_nulls,
    log_null_report,
)

logger = get_logger(__name__, log_file="transform.log")

RAW_FILE = "olist_sellers_dataset.csv"
OUTPUT_FILE = "sellers_cleaned.csv"


def run() -> pd.DataFrame:
    """Execute the full sellers cleaning pipeline."""
    logger.info("── Sellers Cleaning ────────────────────────")

    df = read_csv(RAW_DIR / RAW_FILE)
    log_null_report(df, "sellers_raw")

    before = len(df)
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset=["seller_id"], keep="first")
    logger.info("Duplicate removal: %d → %d rows.", before, len(df))

    df = df.dropna(subset=["seller_id"])

    # Normalise state
    df["seller_state"] = df["seller_state"].str.strip().str.upper()
    invalid = ~df["seller_state"].isin(BRAZIL_STATE_CODES + ["UNKNOWN"])
    if invalid.sum():
        logger.warning("%d sellers have invalid state codes — setting to 'XX'.", invalid.sum())
        df.loc[invalid, "seller_state"] = "XX"

    # Standardise city
    df["seller_city"] = df["seller_city"].str.strip().str.lower().str.title()
    df["seller_city"] = df["seller_city"].fillna("UNKNOWN")

    # Dtypes
    df["seller_id"] = df["seller_id"].astype(str)

    assert_no_duplicate_keys(df, ["seller_id"], "sellers_cleaned")
    assert_no_nulls(df, ["seller_id"], "sellers_cleaned")
    log_null_report(df, "sellers_cleaned")

    ensure_directories(PROCESSED_DIR)
    save_csv(df, PROCESSED_DIR / OUTPUT_FILE)
    logger.info("Sellers cleaning complete. Rows: %d", len(df))
    return df


if __name__ == "__main__":
    run()
