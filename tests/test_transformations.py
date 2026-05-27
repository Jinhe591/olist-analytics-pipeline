"""
tests/test_transformations.py
-----------------------------
Unit tests for all transformation and validation utilities.

Run with:
    pytest tests/ -v
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.validation_utils import (
    assert_date_order,
    assert_foreign_keys,
    assert_no_duplicate_keys,
    assert_no_nulls,
    assert_positive_values,
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture()
def clean_customers_df() -> pd.DataFrame:
    return pd.DataFrame({
        "customer_id":         ["c1", "c2", "c3"],
        "customer_unique_id":  ["u1", "u2", "u3"],
        "customer_city":       ["São Paulo", "Rio De Janeiro", "Belo Horizonte"],
        "customer_state":      ["SP", "RJ", "MG"],
    })


@pytest.fixture()
def orders_df() -> pd.DataFrame:
    return pd.DataFrame({
        "order_id":                     ["o1", "o2"],
        "customer_id":                  ["c1", "c2"],
        "order_purchase_timestamp":     pd.to_datetime(["2018-01-01", "2018-03-15"]),
        "order_estimated_delivery_date": pd.to_datetime(["2018-01-20", "2018-04-01"]),
    })


# ─────────────────────────────────────────────
# Validation utility tests
# ─────────────────────────────────────────────

class TestAssertNoDuplicateKeys:

    def test_passes_on_unique_keys(self, clean_customers_df):
        assert_no_duplicate_keys(clean_customers_df, ["customer_id"], "test")

    def test_fails_on_duplicate_keys(self):
        df = pd.DataFrame({"customer_id": ["c1", "c1", "c2"]})
        with pytest.raises(ValueError, match="duplicate"):
            assert_no_duplicate_keys(df, ["customer_id"], "test")


class TestAssertNoNulls:

    def test_passes_on_complete_column(self, clean_customers_df):
        assert_no_nulls(clean_customers_df, ["customer_id"], "test")

    def test_fails_on_null_values(self):
        df = pd.DataFrame({"customer_id": ["c1", None, "c3"]})
        with pytest.raises(ValueError, match="null"):
            assert_no_nulls(df, ["customer_id"], "test")


class TestAssertPositiveValues:

    def test_passes_on_positive(self):
        df = pd.DataFrame({"revenue": [10.0, 5.5, 100.0]})
        assert_positive_values(df, "revenue", "test")

    def test_fails_on_zero(self):
        df = pd.DataFrame({"revenue": [10.0, 0.0, 5.0]})
        with pytest.raises(ValueError, match="non-positive"):
            assert_positive_values(df, "revenue", "test")

    def test_fails_on_negative(self):
        df = pd.DataFrame({"revenue": [-1.0, 5.0]})
        with pytest.raises(ValueError, match="non-positive"):
            assert_positive_values(df, "revenue", "test")


class TestAssertDateOrder:

    def test_passes_on_valid_dates(self, orders_df):
        assert_date_order(
            orders_df,
            "order_purchase_timestamp",
            "order_estimated_delivery_date",
            "test",
        )

    def test_fails_on_inverted_dates(self):
        df = pd.DataFrame({
            "start": pd.to_datetime(["2018-05-01"]),
            "end":   pd.to_datetime(["2018-01-01"]),
        })
        with pytest.raises(ValueError, match="rows where"):
            assert_date_order(df, "start", "end", "test")

    def test_ignores_null_rows(self):
        df = pd.DataFrame({
            "start": pd.to_datetime(["2018-05-01", None]),
            "end":   pd.to_datetime([None, "2018-01-01"]),
        })
        # Should not raise
        assert_date_order(df, "start", "end", "test")


class TestAssertForeignKeys:

    def test_passes_on_valid_fk(self, clean_customers_df):
        orders = pd.DataFrame({"customer_id": ["c1", "c2"]})
        assert_foreign_keys(orders, "customer_id", clean_customers_df, "customer_id", "test")

    def test_fails_on_orphaned_fk(self, clean_customers_df):
        orders = pd.DataFrame({"customer_id": ["c1", "c99"]})  # c99 not in parent
        with pytest.raises(ValueError, match="orphaned"):
            assert_foreign_keys(
                orders, "customer_id", clean_customers_df, "customer_id", "test"
            )


# ─────────────────────────────────────────────
# Transformation logic tests
# ─────────────────────────────────────────────

class TestCustomersTransformations:

    def test_state_normalisation(self):
        from src.transform.customers_cleaning import normalise_state
        df = pd.DataFrame({"customer_state": ["sp", " RJ ", "invalid_code"]})
        result = normalise_state(df)
        assert result.loc[0, "customer_state"] == "SP"
        assert result.loc[1, "customer_state"] == "RJ"
        assert result.loc[2, "customer_state"] == "XX"

    def test_city_standardisation(self):
        from src.transform.customers_cleaning import standardise_city
        df = pd.DataFrame({"customer_city": ["  SAO PAULO  ", "rio de janeiro"]})
        result = standardise_city(df)
        assert result.loc[0, "customer_city"] == "Sao Paulo"
        assert result.loc[1, "customer_city"] == "Rio De Janeiro"

    def test_duplicate_removal(self):
        from src.transform.customers_cleaning import remove_duplicates
        df = pd.DataFrame({
            "customer_id":        ["c1", "c1", "c2"],
            "customer_unique_id": ["u1", "u1", "u2"],
        })
        result = remove_duplicates(df)
        assert len(result) == 2
        assert result["customer_id"].is_unique


class TestOrdersTransformations:

    def test_timestamp_parsing(self):
        from src.transform.orders_cleaning import parse_timestamps
        df = pd.DataFrame({
            "order_purchase_timestamp": ["2018-01-01 10:00:00", "not_a_date"],
            "order_approved_at": [None, None],
            "order_delivered_carrier_date": [None, None],
            "order_delivered_customer_date": [None, None],
            "order_estimated_delivery_date": [None, None],
        })
        result = parse_timestamps(df)
        assert pd.api.types.is_datetime64_any_dtype(result["order_purchase_timestamp"])
        assert pd.isna(result.loc[1, "order_purchase_timestamp"])

    def test_status_normalisation(self):
        from src.transform.orders_cleaning import normalise_status
        df = pd.DataFrame({"order_status": ["DELIVERED", " shipped ", "fake_status"]})
        result = normalise_status(df)
        assert result.loc[0, "order_status"] == "delivered"
        assert result.loc[1, "order_status"] == "shipped"
        assert result.loc[2, "order_status"] == "unknown"


class TestRevenueEnrichment:

    def test_delivery_duration_positive(self):
        from src.transform.orders_cleaning import compute_delivery_duration
        df = pd.DataFrame({
            "order_purchase_timestamp":     pd.to_datetime(["2018-01-01"]),
            "order_delivered_customer_date": pd.to_datetime(["2018-01-15"]),
            "order_estimated_delivery_date": pd.to_datetime(["2018-01-20"]),
        })
        result = compute_delivery_duration(df)
        assert result.loc[0, "delivery_duration_days"] == 14
        assert result.loc[0, "is_late_delivery"] == False  # noqa: E712

    def test_late_delivery_flag(self):
        from src.transform.orders_cleaning import compute_delivery_duration
        df = pd.DataFrame({
            "order_purchase_timestamp":     pd.to_datetime(["2018-01-01"]),
            "order_delivered_customer_date": pd.to_datetime(["2018-02-01"]),
            "order_estimated_delivery_date": pd.to_datetime(["2018-01-20"]),
        })
        result = compute_delivery_duration(df)
        assert result.loc[0, "is_late_delivery"] == True  # noqa: E712
