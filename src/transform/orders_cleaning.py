"""
orders_cleaning.py
------------------
Cleans and validates the Olist orders dataset.

Transformations applied
-----------------------
- Parse all timestamp columns to datetime
- Normalise order_status values
- Drop orders with null order_id or customer_id
- Remove fully duplicate rows
- Filter logically impossible timestamps
  (e.g. estimated_delivery < purchase_timestamp)
- Flag and optionally remove cancelled/unavailable orders
- Validate delivery duration (< 0 or > 365 days flagged)

Usage
-----
    python -m src.transform.orders_cleaning
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.utils.config import ORDERS_CLEANED, PROCESSED_DIR, RAW_DIR, VALID_ORDER_STATUSES
from src.utils.file_utils import ensure_directories, read_csv, save_csv
from src.utils.logging_utils import get_logger
from src.utils.validation_utils import (
    assert_date_order,
    assert_no_duplicate_keys,
    assert_no_nulls,
    log_null_report,
)

logger = get_logger(__name__, log_file="transform.log")

RAW_FILE = "olist_orders_dataset.csv"

TIMESTAMP_COLS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]


# ─────────────────────────────────────────────
# Transformation steps
# ─────────────────────────────────────────────

def load_raw(raw_dir: Path) -> pd.DataFrame:
    """Load raw orders CSV."""
    return read_csv(raw_dir / RAW_FILE)


def parse_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse all timestamp columns to pandas datetime (UTC-naive).

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    for col in TIMESTAMP_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            n_failed = df[col].isna().sum()
            if n_failed:
                logger.warning("Column '%s': %d values could not be parsed.", col, n_failed)
    logger.info("Timestamp parsing complete.")
    return df


def normalise_status(df: pd.DataFrame) -> pd.DataFrame:
    """
    Lowercase and strip whitespace from order_status.
    Rows with unrecognised statuses are set to 'unknown'.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    df["order_status"] = df["order_status"].str.strip().str.lower()
    invalid = ~df["order_status"].isin(VALID_ORDER_STATUSES)
    if invalid.sum():
        logger.warning(
            "%d orders have unrecognised status — setting to 'unknown'.", invalid.sum()
        )
        df.loc[invalid, "order_status"] = "unknown"
    return df


def drop_critical_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows where order_id or customer_id is null."""
    before = len(df)
    df = df.dropna(subset=["order_id", "customer_id"])
    dropped = before - len(df)
    if dropped:
        logger.warning("Dropped %d rows with null order_id or customer_id.", dropped)
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove fully duplicated rows then duplicate order_id rows."""
    before = len(df)
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset=["order_id"], keep="first")
    logger.info("Duplicate removal: %d → %d rows.", before, len(df))
    return df


def filter_impossible_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove orders where purchase_timestamp is after delivered_customer_date
    or after estimated_delivery_date (both non-null).

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    before = len(df)

    # Purchase must be before estimated delivery
    mask_est = (
        df["order_purchase_timestamp"].notna()
        & df["order_estimated_delivery_date"].notna()
        & (df["order_purchase_timestamp"] > df["order_estimated_delivery_date"])
    )
    if mask_est.sum():
        logger.warning(
            "Removing %d orders where purchase > estimated_delivery.", mask_est.sum()
        )
        df = df[~mask_est]

    # Purchase must be before actual delivery
    mask_act = (
        df["order_purchase_timestamp"].notna()
        & df["order_delivered_customer_date"].notna()
        & (df["order_purchase_timestamp"] > df["order_delivered_customer_date"])
    )
    if mask_act.sum():
        logger.warning(
            "Removing %d orders where purchase > delivered_customer_date.", mask_act.sum()
        )
        df = df[~mask_act]

    logger.info("Timestamp logic filter: %d → %d rows.", before, len(df))
    return df


def compute_delivery_duration(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive delivery_duration_days and is_late_delivery columns.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    delivered = df["order_delivered_customer_date"].notna()
    estimated = df["order_estimated_delivery_date"].notna()
    purchased = df["order_purchase_timestamp"].notna()

    # Actual delivery duration in days (from purchase)
    df["delivery_duration_days"] = np.where(
        delivered & purchased,
        (
            df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
        ).dt.days,
        np.nan,
    )

    # Is late: actual delivery > estimated delivery
    df["is_late_delivery"] = np.where(
        delivered & estimated,
        df["order_delivered_customer_date"] > df["order_estimated_delivery_date"],
        np.nan,
    )

    # Flag extreme delivery durations (> 365 days) as suspicious
    extreme = df["delivery_duration_days"].notna() & (df["delivery_duration_days"] > 365)
    if extreme.sum():
        logger.warning(
            "%d orders have delivery_duration_days > 365 — flagged but retained.",
            extreme.sum(),
        )
    df["suspicious_delivery"] = extreme

    logger.info("Delivery metrics derived.")
    return df


def cast_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure order_id and customer_id are strings."""
    df["order_id"] = df["order_id"].astype(str)
    df["customer_id"] = df["customer_id"].astype(str)
    return df


def validate_output(df: pd.DataFrame) -> None:
    """Post-transformation validation."""
    assert_no_duplicate_keys(df, ["order_id"], "orders_cleaned")
    assert_no_nulls(df, ["order_id", "customer_id", "order_status"], "orders_cleaned")
    assert_date_order(
        df,
        "order_purchase_timestamp",
        "order_estimated_delivery_date",
        "orders_cleaned",
    )
    log_null_report(df, "orders_cleaned")
    logger.info("orders_cleaned validation PASSED. Rows: %d", len(df))


# ─────────────────────────────────────────────
# Pipeline orchestration
# ─────────────────────────────────────────────

def run() -> pd.DataFrame:
    """Execute the full orders cleaning pipeline."""
    logger.info("── Orders Cleaning ─────────────────────────")

    df = load_raw(RAW_DIR)
    log_null_report(df, "orders_raw")

    df = remove_duplicates(df)
    df = drop_critical_nulls(df)
    df = parse_timestamps(df)
    df = normalise_status(df)
    df = filter_impossible_timestamps(df)
    df = compute_delivery_duration(df)
    df = cast_dtypes(df)

    validate_output(df)

    ensure_directories(PROCESSED_DIR)
    save_csv(df, PROCESSED_DIR / ORDERS_CLEANED)

    logger.info("Orders cleaning complete. Output: %s", ORDERS_CLEANED)
    return df


if __name__ == "__main__":
    run()
