"""
tests/test_pipeline_integration.py
-----------------------------------
Integration-style tests that run a mini end-to-end pipeline
on synthetic data — no database connection or Kaggle API required.

These tests verify that every transformation module produces
correct output when given well-formed input.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ─────────────────────────────────────────────
# Mini end-to-end: customers
# ─────────────────────────────────────────────

class TestCustomersPipeline:

    def _make_raw(self) -> pd.DataFrame:
        return pd.DataFrame({
            "customer_id":            ["c1", "c2", "c1", "c3"],  # c1 duplicate
            "customer_unique_id":     ["u1", "u2", "u1", "u3"],
            "customer_zip_code_prefix": ["01310", "20040", "01310", "69000"],
            "customer_city":          ["  SAO PAULO  ", "rio de janeiro", "sao paulo", "MANAUS"],
            "customer_state":         ["sp", "RJ", "sp", "AM"],
        })

    def test_full_pipeline_shape(self):
        from src.transform.customers_cleaning import (
            cast_dtypes, handle_nulls, normalise_state,
            remove_duplicates, standardise_city,
        )
        df = self._make_raw()
        df = remove_duplicates(df)
        df = handle_nulls(df)
        df = normalise_state(df)
        df = standardise_city(df)
        df = cast_dtypes(df)

        # Duplicate c1 removed → 3 rows
        assert len(df) == 3
        assert df["customer_id"].is_unique

    def test_state_values_valid(self):
        from src.transform.customers_cleaning import normalise_state
        df = pd.DataFrame({"customer_state": ["sp", "rj", "INVALID99"]})
        result = normalise_state(df)
        assert result.loc[0, "customer_state"] == "SP"
        assert result.loc[2, "customer_state"] == "XX"

    def test_null_customer_id_dropped(self):
        from src.transform.customers_cleaning import handle_nulls
        df = pd.DataFrame({
            "customer_id":        [None, "c1"],
            "customer_unique_id": ["u0", "u1"],
            "customer_city":      ["x", "y"],
            "customer_state":     ["SP", "RJ"],
        })
        result = handle_nulls(df)
        assert len(result) == 1
        assert result.iloc[0]["customer_id"] == "c1"


# ─────────────────────────────────────────────
# Mini end-to-end: orders
# ─────────────────────────────────────────────

class TestOrdersPipeline:

    def _make_raw(self) -> pd.DataFrame:
        return pd.DataFrame({
            "order_id":                      ["o1", "o2", "o3", "o2"],
            "customer_id":                   ["c1", "c2", "c3", "c2"],
            "order_status":                  ["DELIVERED", "shipped", "CANCELED", "shipped"],
            "order_purchase_timestamp":       [
                "2018-01-01 10:00:00", "2018-03-15 14:00:00",
                "2018-06-01 09:00:00", "2018-03-15 14:00:00",
            ],
            "order_approved_at":              [
                "2018-01-01 10:05:00", "2018-03-15 14:10:00", None, None,
            ],
            "order_delivered_carrier_date":   [
                "2018-01-03 08:00:00", None, None, None,
            ],
            "order_delivered_customer_date":  [
                "2018-01-12 15:00:00", None, None, None,
            ],
            "order_estimated_delivery_date":  [
                "2018-01-20 00:00:00", "2018-04-01 00:00:00",
                "2018-06-20 00:00:00", "2018-04-01 00:00:00",
            ],
        })

    def test_deduplication(self):
        from src.transform.orders_cleaning import remove_duplicates
        df = self._make_raw()
        result = remove_duplicates(df)
        assert len(result) == 3
        assert result["order_id"].is_unique

    def test_status_normalisation(self):
        from src.transform.orders_cleaning import (
            normalise_status, remove_duplicates,
        )
        df = remove_duplicates(self._make_raw())
        result = normalise_status(df)
        assert set(result["order_status"]) <= {
            "delivered", "shipped", "canceled", "unavailable",
            "invoiced", "processing", "approved", "created", "unknown",
        }

    def test_delivery_flag(self):
        from src.transform.orders_cleaning import (
            compute_delivery_duration, parse_timestamps, remove_duplicates,
        )
        df = remove_duplicates(self._make_raw())
        df = parse_timestamps(df)
        df = compute_delivery_duration(df)

        # o1 was delivered before estimated → on-time
        o1 = df[df["order_id"] == "o1"].iloc[0]
        assert o1["is_late_delivery"] == False  # noqa: E712
        assert o1["delivery_duration_days"] == 11

    def test_impossible_timestamp_removed(self):
        from src.transform.orders_cleaning import (
            filter_impossible_timestamps, parse_timestamps,
        )
        df = pd.DataFrame({
            "order_id":                      ["good", "bad"],
            "order_purchase_timestamp":       pd.to_datetime(["2018-01-01", "2018-06-01"]),
            "order_estimated_delivery_date":  pd.to_datetime(["2018-01-20", "2018-01-01"]),
            "order_delivered_customer_date":  [pd.NaT, pd.NaT],
        })
        result = filter_impossible_timestamps(df)
        assert len(result) == 1
        assert result.iloc[0]["order_id"] == "good"


# ─────────────────────────────────────────────
# Mini end-to-end: products
# ─────────────────────────────────────────────

class TestProductsPipeline:

    def _make_raw(self) -> pd.DataFrame:
        return pd.DataFrame({
            "product_id":             ["p1", "p2", "p3", "p1"],
            "product_category_name":  ["beleza_saude", None, "esporte_lazer", "beleza_saude"],
            "product_weight_g":       [300.0, -5.0, 1200.0, 300.0],
            "product_length_cm":      [20.0, 10.0, 40.0, 20.0],
            "product_height_cm":      [10.0, 5.0, 15.0, 10.0],
            "product_width_cm":       [15.0, 8.0, 30.0, 15.0],
        })

    def _make_translation(self) -> pd.DataFrame:
        return pd.DataFrame({
            "product_category_name":         ["beleza_saude", "esporte_lazer"],
            "product_category_name_english": ["health beauty", "sports leisure"],
        })

    def test_deduplication(self):
        from src.transform.products_cleaning import remove_duplicates
        df = self._make_raw()
        result = remove_duplicates(df)
        assert len(result) == 3

    def test_category_translation(self):
        from src.transform.products_cleaning import (
            apply_category_translation, remove_duplicates,
        )
        df = remove_duplicates(self._make_raw())
        result = apply_category_translation(df, self._make_translation())
        p1 = result[result["product_id"] == "p1"].iloc[0]
        assert p1["product_category_name_english"] == "health beauty"

    def test_null_category_filled(self):
        from src.transform.products_cleaning import (
            apply_category_translation, fill_missing_categories,
            remove_duplicates,
        )
        df = remove_duplicates(self._make_raw())
        df = apply_category_translation(df, self._make_translation())
        df = fill_missing_categories(df)
        p2 = df[df["product_id"] == "p2"].iloc[0]
        assert p2["product_category_name_english"] == "uncategorized"

    def test_negative_weight_nulled(self):
        from src.transform.products_cleaning import remove_duplicates, validate_weight
        df = remove_duplicates(self._make_raw())
        result = validate_weight(df)
        p2 = result[result["product_id"] == "p2"].iloc[0]
        assert pd.isna(p2["product_weight_g"])


# ─────────────────────────────────────────────
# Mini end-to-end: revenue enrichment
# ─────────────────────────────────────────────

class TestRevenuePipeline:

    def _make_items(self) -> pd.DataFrame:
        return pd.DataFrame({
            "order_id":      ["o1", "o1", "o2", "o3"],
            "order_item_id": [1, 2, 1, 1],
            "product_id":    ["p1", "p2", "p1", "p3"],
            "seller_id":     ["s1", "s1", "s2", "s3"],
            "price":         [100.0, 50.0, 200.0, 75.0],
            "freight_value": [10.0, 5.0, 20.0, 8.0],
        })

    def _make_payments(self) -> pd.DataFrame:
        return pd.DataFrame({
            "order_id":             ["o1", "o1", "o2", "o3"],
            "payment_type":         ["credit_card", "voucher", "boleto", "credit_card"],
            "payment_value":        [140.0, 25.0, 220.0, 83.0],
            "payment_installments": [3, 1, 1, 2],
        })

    def _make_orders(self) -> pd.DataFrame:
        return pd.DataFrame({
            "order_id":                  ["o1", "o2", "o3"],
            "customer_id":               ["c1", "c2", "c3"],
            "order_status":              ["delivered", "delivered", "canceled"],
            "order_purchase_timestamp":  pd.to_datetime([
                "2018-01-10", "2018-02-15", "2018-03-05",
            ]),
        })

    def test_order_totals(self):
        from src.transform.revenue_enrichment import (
            aggregate_to_order, clean_items, enrich_items,
        )
        items = clean_items(self._make_items())
        items = enrich_items(items)
        agg = aggregate_to_order(items)

        o1 = agg[agg["order_id"] == "o1"].iloc[0]
        assert o1["order_revenue"] == pytest.approx(150.0)
        assert o1["order_item_count"] == 2
        assert o1["order_total"] == pytest.approx(165.0)

    def test_payment_reconciliation_flag(self):
        from src.transform.revenue_enrichment import (
            aggregate_payments, aggregate_to_order, clean_items,
            enrich_items, join_with_payments,
        )
        items = enrich_items(clean_items(self._make_items()))
        order_agg = aggregate_to_order(items)
        payments_agg = aggregate_payments(self._make_payments())
        df = join_with_payments(order_agg, payments_agg)

        # o1: order_total=165, payment=165 → match
        o1 = df[df["order_id"] == "o1"].iloc[0]
        assert o1["revenue_match_flag"] == True  # noqa: E712

    def test_customer_id_joined(self):
        from src.transform.revenue_enrichment import (
            aggregate_payments, aggregate_to_order, clean_items,
            enrich_items, join_with_orders, join_with_payments,
        )
        items = enrich_items(clean_items(self._make_items()))
        order_agg = aggregate_to_order(items)
        payments_agg = aggregate_payments(self._make_payments())
        df = join_with_payments(order_agg, payments_agg)
        df = join_with_orders(df, self._make_orders())

        assert "customer_id" in df.columns
        o2 = df[df["order_id"] == "o2"].iloc[0]
        assert o2["customer_id"] == "c2"
