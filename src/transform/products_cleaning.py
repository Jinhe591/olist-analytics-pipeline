"""
products_cleaning.py
--------------------
Cleans and validates the Olist products dataset.

Transformations applied
-----------------------
- Remove duplicate product_id rows
- Translate category names using the translation lookup table
- Normalise product names (strip whitespace)
- Fill missing categories with 'uncategorized'
- Filter out products with invalid physical dimensions (≤ 0)
- Validate weight_g (must be > 0 where present)
- Cast datatypes

Usage
-----
    python -m src.transform.products_cleaning
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.utils.config import PROCESSED_DIR, PRODUCTS_CLEANED, RAW_DIR
from src.utils.file_utils import ensure_directories, read_csv, save_csv
from src.utils.logging_utils import get_logger
from src.utils.validation_utils import (
    assert_no_duplicate_keys,
    assert_no_nulls,
    log_null_report,
)

logger = get_logger(__name__, log_file="transform.log")

RAW_PRODUCTS = "olist_products_dataset.csv"
RAW_TRANSLATION = "product_category_name_translation.csv"

DIMENSION_COLS = [
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
]


# ─────────────────────────────────────────────
# Transformation steps
# ─────────────────────────────────────────────

def load_raw(raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load products and translation CSV files."""
    products = read_csv(raw_dir / RAW_PRODUCTS)
    translation = read_csv(raw_dir / RAW_TRANSLATION)
    return products, translation


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate product_id rows (keep first)."""
    before = len(df)
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset=["product_id"], keep="first")
    logger.info("Duplicate removal: %d → %d rows.", before, len(df))
    return df


def apply_category_translation(
    df: pd.DataFrame, translation: pd.DataFrame
) -> pd.DataFrame:
    """
    Join English category names from the translation table.
    Falls back to the Portuguese name if no translation exists.
    Fills remaining nulls with 'uncategorized'.

    Parameters
    ----------
    df : pd.DataFrame
    translation : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    translation = translation.rename(
        columns={
            "product_category_name": "category_pt",
            "product_category_name_english": "category_en",
        }
    )
    df = df.merge(
        translation,
        left_on="product_category_name",
        right_on="category_pt",
        how="left",
    )
    # Use English if available, fall back to Portuguese
    df["product_category_name_english"] = np.where(
        df["category_en"].notna(),
        df["category_en"],
        df["product_category_name"],
    )
    df["product_category_name_english"] = (
        df["product_category_name_english"].fillna("uncategorized")
    )
    df = df.drop(columns=["category_pt", "category_en"], errors="ignore")
    logger.info("Category translation applied.")
    return df


def normalise_names(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace from string columns."""
    if "product_category_name" in df.columns:
        df["product_category_name"] = df["product_category_name"].str.strip()
    df["product_category_name_english"] = (
        df["product_category_name_english"]
        .str.strip()
        .str.lower()
        .str.replace("_", " ", regex=False)
    )
    return df


def filter_invalid_dimensions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows where any physical dimension is present but ≤ 0.
    Rows with ALL dimension values missing are kept (dimensions unknown).

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    before = len(df)
    for col in DIMENSION_COLS:
        if col not in df.columns:
            continue
        # Only filter rows where the value IS present but invalid
        invalid = df[col].notna() & (df[col] <= 0)
        if invalid.sum():
            logger.warning("Removing %d rows with %s ≤ 0.", invalid.sum(), col)
            df = df[~invalid]

    logger.info("Dimension filter: %d → %d rows.", before, len(df))
    return df


def validate_weight(df: pd.DataFrame) -> pd.DataFrame:
    """
    Set weight_g to NaN where the recorded value is ≤ 0.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    if "product_weight_g" not in df.columns:
        return df
    invalid = df["product_weight_g"].notna() & (df["product_weight_g"] <= 0)
    if invalid.sum():
        logger.warning("%d rows have weight_g ≤ 0; setting to NaN.", invalid.sum())
        df.loc[invalid, "product_weight_g"] = np.nan
    return df


def fill_missing_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Fill null category names with 'uncategorized'."""
    df["product_category_name_english"] = df[
        "product_category_name_english"
    ].fillna("uncategorized")
    return df


def cast_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Cast columns to appropriate dtypes."""
    df["product_id"] = df["product_id"].astype(str)
    numeric_cols = [
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def validate_output(df: pd.DataFrame) -> None:
    """Post-transformation validation."""
    assert_no_duplicate_keys(df, ["product_id"], "products_cleaned")
    assert_no_nulls(df, ["product_id"], "products_cleaned")
    log_null_report(df, "products_cleaned")
    logger.info("products_cleaned validation PASSED. Rows: %d", len(df))


# ─────────────────────────────────────────────
# Pipeline orchestration
# ─────────────────────────────────────────────

def run() -> pd.DataFrame:
    """Execute the full products cleaning pipeline."""
    logger.info("── Products Cleaning ───────────────────────")

    products, translation = load_raw(RAW_DIR)
    log_null_report(products, "products_raw")

    df = remove_duplicates(products)
    df = apply_category_translation(df, translation)
    df = normalise_names(df)
    df = fill_missing_categories(df)
    df = filter_invalid_dimensions(df)
    df = validate_weight(df)
    df = cast_dtypes(df)

    validate_output(df)

    ensure_directories(PROCESSED_DIR)
    save_csv(df, PROCESSED_DIR / PRODUCTS_CLEANED)

    logger.info("Products cleaning complete. Output: %s", PRODUCTS_CLEANED)
    return df


if __name__ == "__main__":
    run()
