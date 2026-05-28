"""
load_to_sql.py
--------------
Loads all processed CSV files into PostgreSQL staging tables.
Drops dependent views/facts before reloading, then rebuilds them.
"""

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.utils.config import (
    CUSTOMERS_CLEANED,
    DATABASE_URL,
    ORDERS_CLEANED,
    ORDER_REVENUE,
    PROCESSED_DIR,
    PRODUCTS_CLEANED,
)
from src.utils.file_utils import read_csv
from src.utils.logging_utils import get_logger

logger = get_logger(__name__, log_file="load.log")

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# All processed CSVs to load into staging
LOAD_MANIFEST: list[tuple[str, str, list[str]]] = [
    (CUSTOMERS_CLEANED,     "stg_customers", []),
    (PRODUCTS_CLEANED,      "stg_products",  []),
    ("sellers_cleaned.csv", "stg_sellers",   []),
    (
        ORDERS_CLEANED,
        "stg_orders",
        [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    ),
    (
        ORDER_REVENUE,
        "stg_order_revenue",
        ["order_purchase_timestamp"],
    ),
]

# Objects that depend on staging — drop before reload
DEPENDENT_OBJECTS: list[str] = [
    "vw_revenue_by_category",
    "vw_monthly_revenue",
    "vw_revenue_by_state",
    "vw_delivery_performance",
    "vw_customer_kpis",
    "vw_seller_performance",
    "vw_top_products",
    "vw_payment_analysis",
    "vw_order_status_summary",
    "fact_order_items",
    "fact_orders",
    "dim_sellers",
    "dim_products",
    "dim_customers",
]

# SQL files to rebuild after staging reload
REBUILD_SQL_FILES: list[tuple[str, str]] = [
    ("Rebuild dim_customers & products", "sql/dimensions/dim_customers_products.sql"),
    ("Rebuild dim_sellers",              "sql/dimensions/dim_sellers.sql"),
    ("Rebuild fact_orders",              "sql/facts/fact_orders.sql"),
    ("Rebuild fact_order_items",         "sql/facts/fact_order_items.sql"),
    ("Rebuild business views",           "sql/views/business_views.sql"),
    ("Rebuild seller views",             "sql/views/seller_performance_views.sql"),
]


def get_engine():
    """Create and return a SQLAlchemy engine."""
    logger.info("Connecting to database…")
    engine = create_engine(DATABASE_URL, echo=False)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Database connection established.")
    return engine


def drop_dependent_objects(engine) -> None:
    """Drop views and fact tables that depend on staging tables."""
    logger.info("Dropping dependent objects…")
    with engine.connect() as conn:
        for obj in DEPENDENT_OBJECTS:
            conn.execute(text(f"DROP VIEW IF EXISTS {obj} CASCADE"))
            conn.execute(text(f"DROP TABLE IF EXISTS {obj} CASCADE"))
        conn.commit()
    logger.info("Dependent objects dropped.")


def load_table(engine, csv_name: str, table_name: str, datetime_cols: list[str]) -> None:
    """Load a processed CSV file into a staging table."""
    csv_path = PROCESSED_DIR / csv_name
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Processed file not found: {csv_path}\n"
            "Run the transformation pipeline first."
        )

    logger.info("Loading %s → %s", csv_name, table_name)
    df = read_csv(csv_path)

    for col in datetime_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    df.to_sql(
        table_name,
        engine,
        if_exists="replace",
        index=False,
        chunksize=5000,
        method="multi",
    )
    logger.info("Loaded %d rows into %s.", len(df), table_name)


def rebuild_dependent_objects(engine) -> None:
    """Rebuild dimensions, fact tables and views after staging reload."""
    logger.info("Rebuilding dimensions, facts and views…")
    with engine.connect() as conn:
        for label, rel_path in REBUILD_SQL_FILES:
            sql_path = PROJECT_ROOT / rel_path
            if not sql_path.exists():
                logger.warning("SQL file not found, skipping: %s", sql_path)
                continue
            logger.info("  ▶ %s", label)
            sql_text = sql_path.read_text(encoding="utf-8")
            conn.execute(text(sql_text))
            conn.commit()
            logger.info("  ✓ %s", label)
    logger.info("Rebuild complete.")


def run_post_load_validation(engine) -> None:
    """Run basic row-count checks after loading."""
    logger.info("Running post-load row count validation…")
    with engine.connect() as conn:
        for _, table_name, _ in LOAD_MANIFEST:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
            logger.info("  %-25s  %8d rows", table_name, count)


def run() -> None:
    """Orchestrate loading of all staging tables."""
    logger.info("=" * 60)
    logger.info("Staging Load — START")
    logger.info("=" * 60)

    try:
        engine = get_engine()
    except Exception as exc:
        logger.error("Could not connect to database: %s", exc)
        sys.exit(1)

    # Step 1: Drop dependent objects
    try:
        drop_dependent_objects(engine)
    except Exception as exc:
        logger.error("Failed to drop dependent objects: %s", exc)
        sys.exit(1)

    # Step 2: Load all staging tables
    for csv_name, table_name, datetime_cols in LOAD_MANIFEST:
        try:
            load_table(engine, csv_name, table_name, datetime_cols)
        except FileNotFoundError as exc:
            logger.error("File error: %s", exc)
            sys.exit(1)
        except Exception as exc:
            logger.error("Failed to load %s: %s", table_name, exc)
            sys.exit(1)

    # Step 3: Validate row counts
    run_post_load_validation(engine)

    # Step 4: Rebuild dimensions, facts and views
    try:
        rebuild_dependent_objects(engine)
    except Exception as exc:
        logger.warning("Could not rebuild: %s", exc)
        logger.warning("Run run_sql_pipeline.py manually to rebuild.")

    logger.info("=" * 60)
    logger.info("Staging Load — COMPLETE")
    logger.info("=" * 60)


main = run

if __name__ == "__main__":
    run()