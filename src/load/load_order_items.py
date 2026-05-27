"""
load_order_items.py
-------------------
Loads the raw olist_order_items_dataset.csv directly into stg_order_items.
This runs after the staging tables are created (create_stg_order_items.sql).

Usage
-----
    python -m src.load.load_order_items
"""

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.utils.config import DATABASE_URL, RAW_DIR
from src.utils.file_utils import read_csv
from src.utils.logging_utils import get_logger

logger = get_logger(__name__, log_file="load.log")

RAW_FILE = "olist_order_items_dataset.csv"
TABLE_NAME = "stg_order_items"


def run() -> None:
    """Load raw order items into stg_order_items staging table."""
    logger.info("── Load Order Items ────────────────────────")

    csv_path = RAW_DIR / RAW_FILE
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Raw file not found: {csv_path}\n"
            "Run 00_download_dataset.py first."
        )

    df = read_csv(csv_path)

    # Basic type coercions
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    df["freight_value"] = pd.to_numeric(df["freight_value"], errors="coerce").fillna(0.0)
    df["order_item_id"] = pd.to_numeric(df["order_item_id"], errors="coerce")
    df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"], errors="coerce")

    # Drop rows missing composite key
    before = len(df)
    df = df.dropna(subset=["order_id", "order_item_id"])
    df = df.drop_duplicates(subset=["order_id", "order_item_id"])
    logger.info("Rows after dedup: %d → %d", before, len(df))

    engine = create_engine(DATABASE_URL, echo=False)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False,
              chunksize=5000, method="multi")
    logger.info("Loaded %d rows into %s.", len(df), TABLE_NAME)

    # Post-load validation
    with engine.connect() as conn:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME}")).scalar()
    logger.info("Post-load row count: %d", count)
    logger.info("Order items load complete.")


if __name__ == "__main__":
    run()
