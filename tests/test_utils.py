"""
tests/test_utils.py
-------------------
Unit tests for file_utils and config correctness.
"""

import sys
import zipfile
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.config import BRAZIL_STATE_CODES, EXPECTED_RAW_FILES, VALID_ORDER_STATUSES
from src.utils.file_utils import ensure_directories, extract_zip, save_csv, read_csv


# ─────────────────────────────────────────────
# Config sanity tests
# ─────────────────────────────────────────────

class TestConfig:

    def test_brazil_state_codes_count(self):
        """Brazil has 27 states (26 + DF)."""
        assert len(BRAZIL_STATE_CODES) == 27

    def test_all_state_codes_are_two_chars(self):
        for code in BRAZIL_STATE_CODES:
            assert len(code) == 2, f"State code '{code}' is not 2 characters"
            assert code.isupper(), f"State code '{code}' is not uppercase"

    def test_expected_raw_files_nonempty(self):
        assert len(EXPECTED_RAW_FILES) >= 8

    def test_valid_order_statuses_includes_delivered(self):
        assert "delivered" in VALID_ORDER_STATUSES

    def test_valid_order_statuses_includes_canceled(self):
        assert "canceled" in VALID_ORDER_STATUSES


# ─────────────────────────────────────────────
# File utilities tests
# ─────────────────────────────────────────────

class TestEnsureDirectories:

    def test_creates_new_directory(self, tmp_path):
        new_dir = tmp_path / "a" / "b" / "c"
        assert not new_dir.exists()
        ensure_directories(new_dir)
        assert new_dir.exists()

    def test_idempotent_on_existing_directory(self, tmp_path):
        ensure_directories(tmp_path)  # Already exists — should not raise
        assert tmp_path.exists()

    def test_creates_multiple_directories(self, tmp_path):
        dirs = [tmp_path / "x", tmp_path / "y", tmp_path / "z"]
        ensure_directories(*dirs)
        for d in dirs:
            assert d.exists()


class TestExtractZip:

    def test_extracts_valid_zip(self, tmp_path):
        # Create a valid zip with a test file
        zip_path = tmp_path / "test.zip"
        content_file = tmp_path / "hello.txt"
        content_file.write_text("hello world")

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(content_file, arcname="hello.txt")

        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()
        extract_zip(zip_path, extract_dir)

        assert (extract_dir / "hello.txt").exists()

    def test_raises_on_missing_zip(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            extract_zip(tmp_path / "nonexistent.zip", tmp_path)

    def test_raises_on_corrupt_zip(self, tmp_path):
        bad_zip = tmp_path / "bad.zip"
        bad_zip.write_bytes(b"this is not a zip file")
        with pytest.raises(zipfile.BadZipFile):
            extract_zip(bad_zip, tmp_path)


class TestCsvIO:

    def test_save_and_read_roundtrip(self, tmp_path):
        df = pd.DataFrame({
            "id":    ["a", "b", "c"],
            "value": [1.0, 2.0, 3.0],
        })
        path = tmp_path / "test.csv"
        save_csv(df, path)
        loaded = read_csv(path)
        pd.testing.assert_frame_equal(df, loaded)

    def test_save_creates_parent_dir(self, tmp_path):
        df = pd.DataFrame({"x": [1, 2]})
        nested_path = tmp_path / "subdir" / "nested" / "output.csv"
        save_csv(df, nested_path)
        assert nested_path.exists()

    def test_read_csv_returns_dataframe(self, tmp_path):
        csv_path = tmp_path / "simple.csv"
        csv_path.write_text("col1,col2\n1,a\n2,b\n")
        df = read_csv(csv_path)
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["col1", "col2"]
        assert len(df) == 2


# ─────────────────────────────────────────────
# Revenue enrichment unit tests
# ─────────────────────────────────────────────

class TestRevenueLogic:

    def test_order_total_equals_revenue_plus_freight(self):
        """order_total must equal order_revenue + order_freight."""
        from src.transform.revenue_enrichment import aggregate_to_order, enrich_items

        items = pd.DataFrame({
            "order_id":      ["o1", "o1", "o2"],
            "order_item_id": [1, 2, 1],
            "product_id":    ["p1", "p2", "p1"],
            "seller_id":     ["s1", "s1", "s2"],
            "price":         [100.0, 50.0, 200.0],
            "freight_value": [10.0, 5.0, 20.0],
        })
        items = enrich_items(items)
        order_agg = aggregate_to_order(items)

        o1 = order_agg[order_agg["order_id"] == "o1"].iloc[0]
        assert o1["order_revenue"] == pytest.approx(150.0)
        assert o1["order_freight"] == pytest.approx(15.0)
        assert o1["order_total"] == pytest.approx(165.0)
        assert o1["order_item_count"] == 2

    def test_payment_aggregate(self):
        """Payment totals must sum correctly."""
        from src.transform.revenue_enrichment import aggregate_payments

        payments = pd.DataFrame({
            "order_id":           ["o1", "o1", "o2"],
            "payment_type":       ["credit_card", "voucher", "boleto"],
            "payment_value":      [90.0, 10.0, 200.0],
            "payment_installments": [3, 1, 1],
        })
        agg = aggregate_payments(payments)
        o1 = agg[agg["order_id"] == "o1"].iloc[0]
        assert o1["payment_total"] == pytest.approx(100.0)
        assert "credit_card" in o1["payment_types"]
        assert "voucher" in o1["payment_types"]

    def test_negative_price_is_clipped(self):
        """Negative prices must be set to 0 during cleaning."""
        from src.transform.revenue_enrichment import clean_items

        items = pd.DataFrame({
            "order_id":      ["o1"],
            "order_item_id": [1],
            "product_id":    ["p1"],
            "seller_id":     ["s1"],
            "price":         [-50.0],
            "freight_value": [10.0],
        })
        cleaned = clean_items(items)
        assert cleaned.loc[0, "price"] == 0.0
