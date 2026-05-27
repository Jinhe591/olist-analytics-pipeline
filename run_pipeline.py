"""
run_pipeline.py
---------------
Executes the full Olist analytics pipeline end-to-end:
  1. Dataset download (Kaggle API)
  2. Data transformations (cleaning + enrichment)
  3. Load to PostgreSQL staging tables
  4. Build star schema (dimensions, facts, views)
  5. Run validation queries

Usage
-----
    python run_pipeline.py [--skip-download] [--skip-sql]

Options
-------
    --skip-download   Skip Kaggle download if raw files already exist
    --skip-sql        Skip SQL schema build (if already built)
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# ── Auto-load .env file so no manual environment setup is needed ──
load_dotenv(Path(__file__).resolve().parent / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.utils.logging_utils import get_logger

logger = get_logger("pipeline_runner", log_file="pipeline.log")

PROJECT_ROOT = Path(__file__).resolve().parent

# ── SQL files in execution order ─────────────
SQL_STEPS: list[tuple[str, str]] = [
    ("Create stg_order_items",          "sql/staging/create_stg_order_items.sql"),
    ("Create dim_date",                 "sql/dimensions/dim_date.sql"),
    ("Create dim_customers & products", "sql/dimensions/dim_customers_products.sql"),
    ("Create dim_sellers",              "sql/dimensions/dim_sellers.sql"),
    ("Create fact_orders",              "sql/facts/fact_orders.sql"),
    ("Create business views",           "sql/views/business_views.sql"),
    ("Run validation",                  "sql/validation/validate_all.sql"),
]


# ─────────────────────────────────────────────
# Python pipeline step runner
# ─────────────────────────────────────────────

def run_python_step(module_path: str, label: str) -> None:
    """
    Import and execute a pipeline module's run() or main() function.

    Parameters
    ----------
    module_path : str
        Dot-notation module path.
    label : str
        Human-readable step name for logging.
    """
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
        logger.error("✗ Step failed with exit code %s: %s", exc.code, label)
        sys.exit(exc.code or 1)
    except Exception as exc:
        logger.error("✗ Step failed: %s — %s", label, exc)
        sys.exit(1)


# ─────────────────────────────────────────────
# SQL pipeline step runner
# ─────────────────────────────────────────────

def run_sql_step(label: str, sql_rel_path: str, conn) -> None:
    """
    Read and execute a SQL file against the given psycopg2 connection.

    Parameters
    ----------
    label : str
        Human-readable step name.
    sql_rel_path : str
        Path to SQL file relative to project root.
    conn : psycopg2 connection
    """
    sql_path = PROJECT_ROOT / sql_rel_path
    if not sql_path.exists():
        logger.warning("SQL file not found, skipping: %s", sql_path)
        return

    logger.info("▶ SQL: %s", label)
    sql_text = sql_path.read_text(encoding="utf-8")
    try:
        with conn.cursor() as cur:
            cur.execute(sql_text)
        conn.commit()
        logger.info("✓ SQL Complete: %s\n", label)
    except Exception as exc:
        conn.rollback()
        logger.error("✗ SQL Failed: %s — %s", label, exc)
        sys.exit(1)


def run_sql_pipeline() -> None:
    """Connect to PostgreSQL and execute all SQL build steps."""
    try:
        import psycopg2
    except ImportError:
        logger.error("psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)

    db_config = {
        "host":     os.getenv("DB_HOST", "localhost"),
        "port":     int(os.getenv("DB_PORT", "5432")),
        "dbname":   os.getenv("DB_NAME", "olist_db"),
        "user":     os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
    }

    logger.info("Connecting to database for SQL pipeline…")
    try:
        conn = psycopg2.connect(**db_config)
        logger.info("Database connection established.\n")
    except Exception as exc:
        logger.error("Could not connect to database: %s", exc)
        sys.exit(1)

    try:
        for label, rel_path in SQL_STEPS:
            run_sql_step(label, rel_path, conn)
    finally:
        conn.close()
        logger.info("Database connection closed.")


# ─────────────────────────────────────────────
# Main orchestrator
# ─────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Olist E-Commerce Full Pipeline Runner")
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip Kaggle download step (if raw files already exist)",
    )
    parser.add_argument(
        "--skip-sql",
        action="store_true",
        help="Skip SQL schema build (if dimensions/facts already exist)",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("OLIST ANALYTICS PIPELINE — FULL RUN")
    logger.info("=" * 60)

    # ── Phase 1: Python pipeline ───────────────
    logger.info("\n── Phase 1: Data Pipeline ──────────────────")

    python_steps = []

    if not args.skip_download:
        python_steps.append(("src.ingest.00_download_dataset", "Dataset Download"))

    python_steps.extend([
        ("src.transform.customers_cleaning", "Customers Cleaning"),
        ("src.transform.products_cleaning",  "Products Cleaning"),
        ("src.transform.orders_cleaning",    "Orders Cleaning"),
        ("src.transform.revenue_enrichment", "Revenue Enrichment"),
        ("src.load.load_to_sql",             "Load to PostgreSQL"),
    ])

    for module_path, label in python_steps:
        run_python_step(module_path, label)

    # ── Phase 2: SQL schema build ──────────────
    if not args.skip_sql:
        logger.info("\n── Phase 2: Star Schema Build ──────────────")
        run_sql_pipeline()
    else:
        logger.info("\n── Phase 2: Star Schema Build — SKIPPED (--skip-sql) ──")

    # ── Done ───────────────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info("PIPELINE COMPLETE — All steps succeeded.")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Your data is ready in PostgreSQL:")
    logger.info("  Tables : dim_customers, dim_products, dim_date, dim_sellers")
    logger.info("  Facts  : fact_orders")
    logger.info("  Views  : vw_monthly_revenue, vw_revenue_by_category,")
    logger.info("           vw_revenue_by_state, vw_delivery_performance,")
    logger.info("           vw_customer_kpis")
    logger.info("")
    logger.info("Next step: Open Power BI Desktop and connect to:")
    logger.info("  Host: localhost | Database: olist_db | User: postgres")


if __name__ == "__main__":
    main()