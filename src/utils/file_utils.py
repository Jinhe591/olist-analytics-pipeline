"""
file_utils.py
-------------
File-system helpers: directory creation, CSV I/O, ZIP extraction,
and file-existence checks used across the pipeline.
"""

import zipfile
from pathlib import Path

import pandas as pd

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


def ensure_directories(*dirs: Path) -> None:
    """
    Create one or more directories (including parents) if they do not exist.

    Parameters
    ----------
    *dirs : Path
        Variable number of Path objects to create.
    """
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.debug("Directory ensured: %s", d)


def extract_zip(zip_path: Path, extract_to: Path) -> None:
    """
    Extract a ZIP archive to a target directory.

    Parameters
    ----------
    zip_path : Path
        Path to the ZIP file.
    extract_to : Path
        Directory where contents will be extracted.

    Raises
    ------
    zipfile.BadZipFile
        If the ZIP file is corrupted or invalid.
    FileNotFoundError
        If the ZIP file does not exist.
    """
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")

    logger.info("Extracting %s → %s", zip_path.name, extract_to)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)
    logger.info("Extraction complete.")


def validate_files_exist(directory: Path, expected_files: list[str]) -> None:
    """
    Validate that all expected files exist in a directory and are non-empty.

    Parameters
    ----------
    directory : Path
        Directory to check.
    expected_files : list[str]
        List of expected filenames.

    Raises
    ------
    FileNotFoundError
        If any expected file is missing.
    ValueError
        If any file is empty (0 bytes).
    """
    for fname in expected_files:
        fpath = directory / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Expected file missing: {fpath}")
        if fpath.stat().st_size == 0:
            raise ValueError(f"File is empty (0 bytes): {fpath}")
        logger.debug("Validated: %s (%s bytes)", fname, fpath.stat().st_size)
    logger.info("All %d expected files validated.", len(expected_files))


def read_csv(path: Path, **kwargs) -> pd.DataFrame:
    """
    Read a CSV file into a DataFrame with logging.

    Parameters
    ----------
    path : Path
        Path to the CSV file.
    **kwargs
        Additional arguments passed to pd.read_csv.

    Returns
    -------
    pd.DataFrame
    """
    logger.info("Reading CSV: %s", path.name)
    df = pd.read_csv(path, **kwargs)
    logger.info("Loaded %d rows × %d cols from %s", len(df), len(df.columns), path.name)
    return df


def save_csv(df: pd.DataFrame, path: Path, index: bool = False) -> None:
    """
    Save a DataFrame to CSV with logging.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to save.
    path : Path
        Destination path.
    index : bool
        Whether to write the row index. Default False.
    """
    ensure_directories(path.parent)
    df.to_csv(path, index=index)
    logger.info("Saved %d rows → %s", len(df), path.name)
