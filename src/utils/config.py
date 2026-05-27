"""
config.py
---------
Central configuration for the Olist E-Commerce analytics pipeline.
All paths, constants, and environment-driven settings are defined here.
"""

import os
from pathlib import Path

# ─────────────────────────────────────────────
# Project root (two levels up from this file)
# ─────────────────────────────────────────────
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

# ─────────────────────────────────────────────
# Data directories
# ─────────────────────────────────────────────
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DIR: Path = DATA_DIR / "raw"
PROCESSED_DIR: Path = DATA_DIR / "processed"

# ─────────────────────────────────────────────
# Kaggle dataset identifier
# ─────────────────────────────────────────────
KAGGLE_DATASET: str = "olistbr/brazilian-ecommerce"
KAGGLE_ZIP_NAME: str = "brazilian-ecommerce.zip"

# ─────────────────────────────────────────────
# Expected raw CSV files (validates extraction)
# ─────────────────────────────────────────────
EXPECTED_RAW_FILES: list[str] = [
    "olist_customers_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
    "olist_geolocation_dataset.csv",
]

# ─────────────────────────────────────────────
# Processed output filenames
# ─────────────────────────────────────────────
CUSTOMERS_CLEANED: str = "customers_cleaned.csv"
PRODUCTS_CLEANED: str = "products_cleaned.csv"
ORDERS_CLEANED: str = "orders_cleaned.csv"
ORDER_REVENUE: str = "order_revenue.csv"

# ─────────────────────────────────────────────
# Database configuration (env-driven, no secrets in code)
# ─────────────────────────────────────────────
DB_CONFIG: dict = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "olist_db"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

DATABASE_URL: str = (
    f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR: Path = PROJECT_ROOT / "logs"

# ─────────────────────────────────────────────
# Business logic constants
# ─────────────────────────────────────────────
VALID_ORDER_STATUSES: list[str] = [
    "delivered", "shipped", "canceled", "unavailable",
    "invoiced", "processing", "approved", "created",
]

BRAZIL_STATE_CODES: list[str] = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
    "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
    "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]
