"""
00_download_dataset.py
----------------------
Programmatic acquisition of the Olist E-Commerce dataset via the Kaggle API.

Usage
-----
    python -m src.ingest.00_download_dataset

Environment variables required
-------------------------------
    KAGGLE_USERNAME  – Kaggle account username
    KAGGLE_KEY       – Kaggle API key

    Alternatively, place ~/.kaggle/kaggle.json with the same credentials.

The script is idempotent: if raw CSV files already exist it skips the download.
"""

import os
import sys
import zipfile
from pathlib import Path

# Allow running as a standalone script
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.utils.config import (
    EXPECTED_RAW_FILES,
    KAGGLE_DATASET,
    KAGGLE_ZIP_NAME,
    RAW_DIR,
)
from src.utils.file_utils import ensure_directories, validate_files_exist
from src.utils.logging_utils import get_logger

logger = get_logger(__name__, log_file="ingest.log")


# ─────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────

def _check_kaggle_credentials() -> None:
    """
    Verify Kaggle credentials are available either via environment variables
    or the ~/.kaggle/kaggle.json file.

    Raises
    ------
    EnvironmentError
        If credentials are not found in either location.
    """
    has_env = os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY")
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    has_json = kaggle_json.exists()

    if not has_env and not has_json:
        raise EnvironmentError(
            "Kaggle credentials not found.\n"
            "Option 1: Set environment variables KAGGLE_USERNAME and KAGGLE_KEY.\n"
            "Option 2: Place your kaggle.json at ~/.kaggle/kaggle.json.\n"
            "Download kaggle.json from: https://www.kaggle.com/settings → API."
        )

    if has_env:
        logger.info("Kaggle credentials sourced from environment variables.")
    else:
        logger.info("Kaggle credentials sourced from ~/.kaggle/kaggle.json.")


def _files_already_downloaded(raw_dir: Path, expected_files: list[str]) -> bool:
    """
    Return True if all expected CSV files already exist and are non-empty.

    Parameters
    ----------
    raw_dir : Path
    expected_files : list[str]

    Returns
    -------
    bool
    """
    return all(
        (raw_dir / f).exists() and (raw_dir / f).stat().st_size > 0
        for f in expected_files
    )


def _download_dataset(raw_dir: Path) -> Path:
    """
    Download the Olist dataset ZIP via the Kaggle API.

    Parameters
    ----------
    raw_dir : Path
        Directory where the ZIP will be saved.

    Returns
    -------
    Path
        Path to the downloaded ZIP file.

    Raises
    ------
    RuntimeError
        If the download fails or the ZIP is not found after download.
    """
    try:
        import kaggle  # noqa: PLC0415 – intentional late import
    except ImportError as exc:
        raise ImportError(
            "The 'kaggle' package is not installed. "
            "Run: pip install kaggle"
        ) from exc

    logger.info("Starting download: dataset=%s", KAGGLE_DATASET)
    try:
        kaggle.api.dataset_download_files(
            KAGGLE_DATASET,
            path=str(raw_dir),
            unzip=False,
            quiet=False,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Kaggle download failed: {exc}\n"
            "Check your internet connection and Kaggle API credentials."
        ) from exc

    zip_path = raw_dir / KAGGLE_ZIP_NAME
    if not zip_path.exists():
        # Some versions of the Kaggle library name the file differently
        zips = list(raw_dir.glob("*.zip"))
        if not zips:
            raise RuntimeError(
                f"Download appeared to succeed but no ZIP file found in {raw_dir}."
            )
        zip_path = zips[0]
        logger.warning("ZIP found with different name: %s", zip_path.name)

    logger.info("Download complete: %s (%d bytes)", zip_path.name, zip_path.stat().st_size)
    return zip_path


def _extract_dataset(zip_path: Path, extract_to: Path) -> None:
    """
    Extract a ZIP archive and validate integrity.

    Parameters
    ----------
    zip_path : Path
    extract_to : Path

    Raises
    ------
    zipfile.BadZipFile
        If the archive is corrupted.
    """
    logger.info("Extracting %s → %s", zip_path.name, extract_to)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.testzip()  # Validate integrity before extraction
            zf.extractall(extract_to)
    except zipfile.BadZipFile as exc:
        raise zipfile.BadZipFile(
            f"The downloaded file '{zip_path.name}' is corrupted. "
            "Try deleting it and re-running the script."
        ) from exc

    logger.info("Extraction complete.")


# ─────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────

def main() -> None:
    """
    Orchestrate dataset acquisition:
    1. Check credentials
    2. Skip if already downloaded
    3. Download ZIP
    4. Extract ZIP
    5. Validate extracted files
    """
    logger.info("=" * 60)
    logger.info("Olist Dataset Acquisition — START")
    logger.info("=" * 60)

    # ── Step 1: Validate credentials ──────────
    try:
        _check_kaggle_credentials()
    except EnvironmentError as exc:
        logger.error("Credential check failed: %s", exc)
        sys.exit(1)

    # ── Step 2: Ensure directories exist ──────
    ensure_directories(RAW_DIR)

    # ── Step 3: Skip if already present ───────
    if _files_already_downloaded(RAW_DIR, EXPECTED_RAW_FILES):
        logger.info("All expected files already present in %s. Skipping download.", RAW_DIR)
        logger.info("Olist Dataset Acquisition — SKIPPED (already up-to-date)")
        return

    # ── Step 4: Download ───────────────────────
    try:
        zip_path = _download_dataset(RAW_DIR)
    except (ImportError, RuntimeError, PermissionError) as exc:
        logger.error("Download failed: %s", exc)
        sys.exit(1)

    # ── Step 5: Extract ────────────────────────
    try:
        _extract_dataset(zip_path, RAW_DIR)
    except (zipfile.BadZipFile, PermissionError) as exc:
        logger.error("Extraction failed: %s", exc)
        sys.exit(1)

    # ── Step 6: Validate ───────────────────────
    try:
        validate_files_exist(RAW_DIR, EXPECTED_RAW_FILES)
    except (FileNotFoundError, ValueError) as exc:
        logger.error("Post-extraction validation failed: %s", exc)
        sys.exit(1)

    # ── Cleanup ZIP ────────────────────────────
    try:
        zip_path.unlink()
        logger.info("Removed ZIP archive to save space.")
    except OSError as exc:
        logger.warning("Could not remove ZIP: %s", exc)

    logger.info("=" * 60)
    logger.info("Olist Dataset Acquisition — COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
