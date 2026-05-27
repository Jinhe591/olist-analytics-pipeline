"""
customers_cleaning.py
---------------------
Cleans and validates the Olist customers dataset.

Transformations applied
-----------------------
- Remove duplicate customer_id rows
- Normalise customer_state to uppercase 2-letter codes
- Standardise city names (strip whitespace, title-case)
- Drop rows with null customer_id
- Validate customer_state against known Brazilian state codes
- Cast datatypes
- Write validated output to processed/customers_cleaned.csv

Usage
-----
    python -m src.transform.customers_cleaning
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.utils.config import (
    BRAZIL_STATE_CODES,
    CUSTOMERS_CLEANED,
    PROCESSED_DIR,
    RAW_DIR,
)
from src.utils.file_utils import ensure_directories, read_csv, save_csv
from src.utils.logging_utils import get_logger
from src.utils.validation_utils import (
    assert_no_duplicate_keys,
    assert_no_nulls,
    log_null_report,
)

logger = get_logger(__name__, log_file="transform.log")

RAW_FILE = "olist_customers_dataset.csv"


# ─────────────────────────────────────────────
# Transformation steps
# ─────────────────────────────────────────────

def load_raw(raw_dir: Path) -> pd.DataFrame:
    """Load raw customers CSV."""
    return read_csv(raw_dir / RAW_FILE)


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove fully duplicated rows and rows with duplicate customer_id.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    before = len(df)
    df = df.drop_duplicates()
    # Keep first occurrence of each customer_unique_id
    df = df.drop_duplicates(subset=["customer_id"], keep="first")
    removed = before - len(df)
    logger.info("Duplicate removal: %d rows removed. Remaining: %d", removed, len(df))
    return df


def handle_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows where customer_id is null.
    Fill missing city/state with UNKNOWN.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    before = len(df)
    df = df.dropna(subset=["customer_id"])
    dropped = before - len(df)
    if dropped:
        logger.warning("Dropped %d rows with null customer_id.", dropped)

    df["customer_city"] = df["customer_city"].fillna("UNKNOWN")
    df["customer_state"] = df["customer_state"].fillna("UNKNOWN")
    return df


def normalise_state(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise customer_state to uppercase 2-letter codes.
    Rows with invalid state codes are flagged with state = 'XX'.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    df["customer_state"] = df["customer_state"].str.strip().str.upper()
    invalid_mask = ~df["customer_state"].isin(BRAZIL_STATE_CODES + ["UNKNOWN"])
    n_invalid = invalid_mask.sum()
    if n_invalid:
        logger.warning(
            "%d rows have unrecognised state codes — setting to 'XX'.", n_invalid
        )
        df.loc[invalid_mask, "customer_state"] = "XX"
    return df


def standardise_city(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strip whitespace and apply title-case to customer_city.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    df["customer_city"] = (
        df["customer_city"]
        .str.strip()
        .str.lower()
        .str.title()
    )
    return df


def cast_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure correct Python/Pandas dtypes.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    str_cols = [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)
    return df


def validate_output(df: pd.DataFrame) -> None:
    """
    Run post-transformation validation checks.

    Parameters
    ----------
    df : pd.DataFrame

    Raises
    ------
    ValueError
        On any critical validation failure.
    """
    assert_no_duplicate_keys(df, ["customer_id"], "customers_cleaned")
    assert_no_nulls(df, ["customer_id", "customer_unique_id"], "customers_cleaned")
    log_null_report(df, "customers_cleaned")
    logger.info("customers_cleaned validation PASSED. Rows: %d", len(df))


# ─────────────────────────────────────────────
# Pipeline orchestration
# ─────────────────────────────────────────────

def run() -> pd.DataFrame:
    """
    Execute the full customers cleaning pipeline.

    Returns
    -------
    pd.DataFrame
        Cleaned customers DataFrame.
    """
    logger.info("── Customers Cleaning ──────────────────────")

    df = load_raw(RAW_DIR)
    log_null_report(df, "customers_raw")

    df = remove_duplicates(df)
    df = handle_nulls(df)
    df = normalise_state(df)
    df = standardise_city(df)
    df = cast_dtypes(df)

    validate_output(df)

    ensure_directories(PROCESSED_DIR)
    save_csv(df, PROCESSED_DIR / CUSTOMERS_CLEANED)

    logger.info("Customers cleaning complete. Output: %s", CUSTOMERS_CLEANED)
    return df


if __name__ == "__main__":
    run()
