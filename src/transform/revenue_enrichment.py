"""
revenue_enrichment.py
---------------------
Joins order_items with payments and orders to produce an enriched
revenue dataset at order-item grain, plus order-level aggregates.

Derived metrics
---------------
- item_revenue        : price per item
- item_freight        : freight_value per item
- total_item_value    : price + freight_value per item
- order_revenue       : sum of price across items in the same order
- order_freight       : sum of freight_value across items in the same order
- order_total         : order_revenue + order_freight
- order_item_count    : number of items in the order
- payment_total       : total payment value from payments table
- revenue_match_flag  : True if order_total ≈ payment_total (within 1 BRL tolerance)

Usage
-----
    python -m src.transform.revenue_enrichment
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.utils.config import ORDER_REVENUE, PROCESSED_DIR, RAW_DIR
from src.utils.file_utils import ensure_directories, read_csv, save_csv
from src.utils.logging_utils import get_logger
from src.utils.validation_utils import (
    assert_no_duplicate_keys,
    assert_no_nulls,
    assert_positive_values,
    log_null_report,
)

logger = get_logger(__name__, log_file="transform.log")

RAW_ITEMS = "olist_order_items_dataset.csv"
RAW_PAYMENTS = "olist_order_payments_dataset.csv"
RAW_ORDERS = "olist_orders_dataset.csv"

REVENUE_TOLERANCE = 1.0  # BRL tolerance for payment reconciliation


# ─────────────────────────────────────────────
# Transformation steps
# ─────────────────────────────────────────────

def load_raw(raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load order items, payments, and orders CSVs."""
    items = read_csv(raw_dir / RAW_ITEMS)
    payments = read_csv(raw_dir / RAW_PAYMENTS)
    orders = read_csv(raw_dir / RAW_ORDERS)
    return items, payments, orders


def clean_items(items: pd.DataFrame) -> pd.DataFrame:
    """
    Basic cleaning on order_items:
    - Remove duplicates
    - Drop rows with null order_id or product_id
    - Ensure price and freight_value are numeric and ≥ 0
    """
    before = len(items)
    items = items.drop_duplicates()
    items = items.dropna(subset=["order_id", "product_id"])
    items["price"] = pd.to_numeric(items["price"], errors="coerce").fillna(0.0)
    items["freight_value"] = pd.to_numeric(
        items["freight_value"], errors="coerce"
    ).fillna(0.0)

    # Clip negative prices/freight to 0
    neg_price = (items["price"] < 0).sum()
    neg_freight = (items["freight_value"] < 0).sum()
    if neg_price:
        logger.warning("%d items have negative price — setting to 0.", neg_price)
        items.loc[items["price"] < 0, "price"] = 0.0
    if neg_freight:
        logger.warning(
            "%d items have negative freight_value — setting to 0.", neg_freight
        )
        items.loc[items["freight_value"] < 0, "freight_value"] = 0.0

    logger.info("Items cleaned: %d → %d rows.", before, len(items))
    return items


def aggregate_payments(payments: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate payments to order level (sum of payment_value).

    Parameters
    ----------
    payments : pd.DataFrame

    Returns
    -------
    pd.DataFrame
        One row per order_id with columns: order_id, payment_total, payment_types.
    """
    payments["payment_value"] = pd.to_numeric(
        payments["payment_value"], errors="coerce"
    ).fillna(0.0)

    agg = payments.groupby("order_id").agg(
        payment_total=("payment_value", "sum"),
        payment_types=("payment_type", lambda x: "|".join(sorted(set(x.dropna())))),
        payment_installments=("payment_installments", "max"),
    ).reset_index()
    return agg


def enrich_items(items: pd.DataFrame) -> pd.DataFrame:
    """
    Add per-item revenue columns.

    Parameters
    ----------
    items : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    items["item_revenue"] = items["price"]
    items["item_freight"] = items["freight_value"]
    items["total_item_value"] = items["price"] + items["freight_value"]
    return items


def aggregate_to_order(items: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate item-level data to order level.

    Parameters
    ----------
    items : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    order_agg = items.groupby("order_id").agg(
        order_revenue=("price", "sum"),
        order_freight=("freight_value", "sum"),
        order_item_count=("order_item_id", "count"),
        unique_products=("product_id", "nunique"),
        unique_sellers=("seller_id", "nunique"),
    ).reset_index()

    order_agg["order_total"] = order_agg["order_revenue"] + order_agg["order_freight"]
    return order_agg


def join_with_payments(
    order_agg: pd.DataFrame, payments_agg: pd.DataFrame
) -> pd.DataFrame:
    """
    Left-join order aggregates with payment aggregates.
    Adds a flag where total doesn't reconcile with payment.

    Parameters
    ----------
    order_agg : pd.DataFrame
    payments_agg : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    df = order_agg.merge(payments_agg, on="order_id", how="left")

    # Reconciliation flag
    df["revenue_match_flag"] = np.where(
        df["payment_total"].notna(),
        abs(df["order_total"] - df["payment_total"]) <= REVENUE_TOLERANCE,
        np.nan,
    )

    mismatch = (~df["revenue_match_flag"].astype(bool)) & df["payment_total"].notna()
    logger.info(
        "Revenue reconciliation: %d mismatches (tolerance=%.2f BRL)",
        mismatch.sum(),
        REVENUE_TOLERANCE,
    )
    return df


def join_with_orders(
    df: pd.DataFrame, orders: pd.DataFrame
) -> pd.DataFrame:
    """
    Join with orders to add status and purchase timestamp.

    Parameters
    ----------
    df : pd.DataFrame
    orders : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    orders_slim = orders[
        ["order_id", "customer_id", "order_status", "order_purchase_timestamp"]
    ].copy()
    orders_slim["order_purchase_timestamp"] = pd.to_datetime(
        orders_slim["order_purchase_timestamp"], errors="coerce"
    )
    df = df.merge(orders_slim, on="order_id", how="left")
    return df


def validate_output(df: pd.DataFrame) -> None:
    """Post-transformation validation."""
    assert_no_duplicate_keys(df, ["order_id"], "order_revenue")
    assert_no_nulls(df, ["order_id"], "order_revenue")

    # Revenue totals must be ≥ 0 (orders can be 0 if only freight)
    neg_revenue = (df["order_revenue"] < 0).sum()
    if neg_revenue:
        raise ValueError(
            f"[order_revenue] {neg_revenue} orders have negative order_revenue."
        )

    log_null_report(df, "order_revenue")
    logger.info("order_revenue validation PASSED. Rows: %d", len(df))

    # Summary stats
    logger.info(
        "Revenue summary — total: %.2f BRL | mean AOV: %.2f BRL | max: %.2f BRL",
        df["order_revenue"].sum(),
        df["order_revenue"].mean(),
        df["order_revenue"].max(),
    )


# ─────────────────────────────────────────────
# Pipeline orchestration
# ─────────────────────────────────────────────

def run() -> pd.DataFrame:
    """Execute the full revenue enrichment pipeline."""
    logger.info("── Revenue Enrichment ──────────────────────")

    items, payments, orders = load_raw(RAW_DIR)

    items = clean_items(items)
    items = enrich_items(items)

    payments_agg = aggregate_payments(payments)
    order_agg = aggregate_to_order(items)

    df = join_with_payments(order_agg, payments_agg)
    df = join_with_orders(df, orders)

    validate_output(df)

    ensure_directories(PROCESSED_DIR)
    save_csv(df, PROCESSED_DIR / ORDER_REVENUE)

    logger.info("Revenue enrichment complete. Output: %s", ORDER_REVENUE)
    return df


if __name__ == "__main__":
    run()
