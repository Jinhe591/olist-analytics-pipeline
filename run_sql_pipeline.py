"""
run_sql_pipeline.py
-------------------
Executes all SQL scripts in the correct order against the configured
PostgreSQL database.

Usage
-----
    python run_sql_pipeline.py [--validate-only]

Options
-------
    --validate-only   Run only the validation queries (skip DDL/DML)
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

import psycopg2
from psycopg2 import sql as pg_sql

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.utils.config import DB_CONFIG
from src.utils.logging_utils import get_logger

logger = get_logger("sql_pipeline", log_file="sql_pipeline.log")

PROJECT_ROOT = Path(__file__).resolve().parent

# ── Ordered SQL execution plan ───────────────
SQL_STEPS: list[tuple[str, str]] = [
    # label,  relative path from project root
    ("Create stg_order_items",      "sql/staging/create_stg_order_items.sql"),
    ("Create dim_date",             "sql/dimensions/dim_date.sql"),
    ("Create dim_customers/products", "sql/dimensions/dim_customers_products.sql"),
    ("Create dim_sellers",          "sql/dimensions/dim_sellers.sql"),
    ("Create fact_orders",          "sql/facts/fact_orders.sql"),
    ("Create fact_order_items",     "sql/facts/fact_order_items.sql"),
    ("Create business views",       "sql/views/business_views.sql"),
]

VALIDATION_STEPS: list[tuple[str, str]] = [
    ("Validate all (order grain)",  "sql/validation/validate_all.sql"),
    ("Validate item level",         "sql/validation/validate_item_level.sql"),
]


def get_connection():
    """Return a psycopg2 connection using DB_CONFIG."""
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )


def execute_sql_file(conn, sql_path: Path, label: str) -> None:
    """
    Read and execute a SQL file against the given connection.

    Parameters
    ----------
    conn : psycopg2 connection
    sql_path : Path
    label : str
    """
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    sql_text = sql_path.read_text(encoding="utf-8")
    logger.info("▶ %s", label)

    with conn.cursor() as cur:
        cur.execute(sql_text)
    conn.commit()
    logger.info("✓ %s", label)


def run_steps(steps: list[tuple[str, str]], conn) -> None:
    """Run a list of (label, path) SQL steps."""
    for label, rel_path in steps:
        sql_path = PROJECT_ROOT / rel_path
        try:
            execute_sql_file(conn, sql_path, label)
        except Exception as exc:
            logger.error("✗ Failed: %s\n  Error: %s", label, exc)
            conn.rollback()
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Olist SQL Pipeline Runner")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only run validation queries",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("OLIST SQL PIPELINE")
    logger.info("=" * 60)

    try:
        conn = get_connection()
        logger.info("Connected to database: %s@%s/%s",
                    DB_CONFIG["user"], DB_CONFIG["host"], DB_CONFIG["database"])
    except Exception as exc:
        logger.error("Database connection failed: %s", exc)
        sys.exit(1)

    try:
        if not args.validate_only:
            logger.info("\n── Schema Build ────────────────────────────")
            run_steps(SQL_STEPS, conn)

        logger.info("\n── Validation ──────────────────────────────")
        run_steps(VALIDATION_STEPS, conn)

    finally:
        conn.close()

    logger.info("=" * 60)
    logger.info("SQL PIPELINE COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()