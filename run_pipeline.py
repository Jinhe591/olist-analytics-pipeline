"""
run_pipeline.py
---------------
Full Olist pipeline - runs everything in correct order.
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.utils.logging_utils import get_logger

logger = get_logger("pipeline_runner", log_file="pipeline.log")

PROJECT_ROOT = Path(__file__).resolve().parent

# Each group is committed separately to avoid dependency issues
SQL_GROUPS: list[tuple[str, list[tuple[str, str]]]] = [
    ("Staging structures", [
        ("Create stg_order_items table", "sql/staging/create_stg_order_items.sql"),
    ]),
    ("Dimensions", [
        ("Create dim_date",                 "sql/dimensions/dim_date.sql"),
        ("Create dim_customers & products", "sql/dimensions/dim_customers_products.sql"),
        ("Create dim_sellers",              "sql/dimensions/dim_sellers.sql"),
    ]),
    ("Facts", [
        ("Create fact_orders",      "sql/facts/fact_orders.sql"),
        ("Create fact_order_items", "sql/facts/fact_order_items.sql"),
    ]),
    ("Views", [
        ("Create business views", "sql/views/business_views.sql"),
        ("Create seller views",   "sql/views/seller_performance_views.sql"),
    ]),
    ("Validation", [
        ("Run validation", "sql/validation/validate_all.sql"),
    ]),
]


def get_db_connection():
    import psycopg2
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "olist_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def run_python_step(module_path: str, label: str) -> None:
    import importlib
    logger.info("▶ Running: %s", label)
    try:
        module = importlib.import_module(module_path)
        fn = getattr(module, "run", None) or getattr(module, "main", None)
        if fn is None:
            raise AttributeError(f"Module {module_path} has no run() or main() function.")
        fn()
        logger.info("✓ Completed: %s\n", label)
    except SystemExit as exc:
        logger.error("✗ Failed: %s (exit code %s)", label, exc.code)
        sys.exit(exc.code or 1)
    except Exception as exc:
        logger.error("✗ Failed: %s — %s", label, exc)
        sys.exit(1)


def run_sql_group(group_name: str, steps: list[tuple[str, str]]) -> None:
    """Run a group of SQL files in a single connection with commit after each."""
    logger.info("\n── SQL Group: %s ────────────────────────", group_name)
    try:
        conn = get_db_connection()
    except Exception as exc:
        logger.error("Database connection failed: %s", exc)
        sys.exit(1)

    try:
        for label, rel_path in steps:
            sql_path = PROJECT_ROOT / rel_path
            if not sql_path.exists():
                logger.error("SQL file not found: %s", sql_path)
                conn.close()
                sys.exit(1)
            logger.info("▶ SQL: %s", label)
            try:
                with conn.cursor() as cur:
                    cur.execute(sql_path.read_text(encoding="utf-8"))
                conn.commit()
                logger.info("✓ SQL Complete: %s", label)
            except Exception as exc:
                conn.rollback()
                logger.error("✗ SQL Failed: %s — %s", label, exc)
                conn.close()
                sys.exit(1)
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Olist Full Pipeline")
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--skip-sql", action="store_true")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("OLIST ANALYTICS PIPELINE — FULL RUN")
    logger.info("=" * 60)

    # ── Phase 1a: Transformations ──────────────
    logger.info("\n── Phase 1a: Transformations ───────────────")
    steps = []
    if not args.skip_download:
        steps.append(("src.ingest.00_download_dataset", "Dataset Download"))
    steps.extend([
        ("src.transform.customers_cleaning", "Customers Cleaning"),
        ("src.transform.products_cleaning",  "Products Cleaning"),
        ("src.transform.orders_cleaning",    "Orders Cleaning"),
        ("src.transform.revenue_enrichment", "Revenue Enrichment"),
        ("src.transform.sellers_cleaning",   "Sellers Cleaning"),
    ])
    for module_path, label in steps:
        run_python_step(module_path, label)

    # ── Phase 1b: Create stg_order_items ───────
    # Must run BEFORE loading order items
    run_sql_group("Staging structures", SQL_GROUPS[0][1])

    # ── Phase 1c: Load all staging tables ──────
    logger.info("\n── Phase 1c: Load Staging Tables ───────────")
    run_python_step("src.load.load_to_sql",      "Load Main Staging Tables")
    run_python_step("src.load.load_order_items", "Load Order Items")

    # ── Phase 2: Build star schema ─────────────
    if not args.skip_sql:
        # Run each group separately with its own connection + commit
        # This ensures each layer exists before the next layer references it
        for group_name, group_steps in SQL_GROUPS[1:]:  # skip staging (already done)
            run_sql_group(group_name, group_steps)

    # ── Done ───────────────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info("PIPELINE COMPLETE — All steps succeeded.")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Tables ready in PostgreSQL:")
    logger.info("  Staging : stg_customers, stg_products, stg_orders,")
    logger.info("            stg_order_revenue, stg_order_items, stg_sellers")
    logger.info("  Dims    : dim_customers, dim_products, dim_date, dim_sellers")
    logger.info("  Facts   : fact_orders, fact_order_items")
    logger.info("  Views   : vw_monthly_revenue, vw_revenue_by_category,")
    logger.info("            vw_revenue_by_state, vw_delivery_performance,")
    logger.info("            vw_customer_kpis")
    logger.info("")
    logger.info("Next: Power BI → Home → Refresh")


if __name__ == "__main__":
    main()