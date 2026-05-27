"""
validation_utils.py
-------------------
Reusable DataFrame validation functions used across the pipeline.
Raises ValueError with descriptive messages on any validation failure.
"""

import pandas as pd

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


def assert_no_duplicate_keys(df: pd.DataFrame, key_cols: list[str], label: str) -> None:
    """
    Raise ValueError if duplicate values exist on key columns.

    Parameters
    ----------
    df : pd.DataFrame
    key_cols : list[str]
        Column(s) forming the primary key.
    label : str
        Human-readable name for error messages.
    """
    n_dupes = df.duplicated(subset=key_cols).sum()
    if n_dupes > 0:
        raise ValueError(
            f"[{label}] {n_dupes} duplicate rows found on key {key_cols}."
        )
    logger.info("[%s] No duplicate keys on %s. ✓", label, key_cols)


def assert_no_nulls(df: pd.DataFrame, cols: list[str], label: str) -> None:
    """
    Raise ValueError if any required column contains nulls.

    Parameters
    ----------
    df : pd.DataFrame
    cols : list[str]
        Columns that must be non-null.
    label : str
        Human-readable dataset name.
    """
    for col in cols:
        null_count = df[col].isna().sum()
        if null_count > 0:
            raise ValueError(
                f"[{label}] Column '{col}' has {null_count} null values."
            )
    logger.info("[%s] Required columns %s are non-null. ✓", label, cols)


def assert_positive_values(df: pd.DataFrame, col: str, label: str) -> None:
    """
    Raise ValueError if any value in a numeric column is ≤ 0.

    Parameters
    ----------
    df : pd.DataFrame
    col : str
        Column to validate.
    label : str
        Human-readable dataset name.
    """
    non_positive = (df[col] <= 0).sum()
    if non_positive > 0:
        raise ValueError(
            f"[{label}] Column '{col}' has {non_positive} non-positive values."
        )
    logger.info("[%s] Column '%s' values are all positive. ✓", label, col)


def assert_date_order(
    df: pd.DataFrame,
    earlier_col: str,
    later_col: str,
    label: str,
    allow_equal: bool = True,
) -> None:
    """
    Raise ValueError if earlier_col > later_col (ignoring nulls).

    Parameters
    ----------
    df : pd.DataFrame
    earlier_col : str
        Column that must be the earlier timestamp.
    later_col : str
        Column that must be the later timestamp.
    label : str
        Human-readable dataset name.
    allow_equal : bool
        Whether equal timestamps are acceptable. Default True.
    """
    mask = df[earlier_col].notna() & df[later_col].notna()
    if allow_equal:
        violations = (df.loc[mask, earlier_col] > df.loc[mask, later_col]).sum()
    else:
        violations = (df.loc[mask, earlier_col] >= df.loc[mask, later_col]).sum()

    if violations > 0:
        raise ValueError(
            f"[{label}] {violations} rows where '{earlier_col}' > '{later_col}'."
        )
    logger.info(
        "[%s] Date order %s ≤ %s validated. ✓", label, earlier_col, later_col
    )


def assert_foreign_keys(
    child_df: pd.DataFrame,
    child_col: str,
    parent_df: pd.DataFrame,
    parent_col: str,
    label: str,
) -> None:
    """
    Raise ValueError if child_col contains values absent in parent_col.

    Parameters
    ----------
    child_df : pd.DataFrame
    child_col : str
    parent_df : pd.DataFrame
    parent_col : str
    label : str
    """
    orphans = ~child_df[child_col].isin(parent_df[parent_col])
    n_orphans = orphans.sum()
    if n_orphans > 0:
        raise ValueError(
            f"[{label}] {n_orphans} orphaned foreign key values in '{child_col}'."
        )
    logger.info(
        "[%s] Foreign key '%s' → '%s' validated. ✓", label, child_col, parent_col
    )


def log_null_report(df: pd.DataFrame, label: str) -> None:
    """
    Log null counts and percentages for every column.

    Parameters
    ----------
    df : pd.DataFrame
    label : str
    """
    total = len(df)
    null_counts = df.isna().sum()
    null_pct = (null_counts / total * 100).round(2)
    report = null_counts[null_counts > 0]

    if report.empty:
        logger.info("[%s] No null values found in any column.", label)
    else:
        logger.info("[%s] Null value report:", label)
        for col, cnt in report.items():
            logger.info("  %-40s  %6d  (%5.2f%%)", col, cnt, null_pct[col])
