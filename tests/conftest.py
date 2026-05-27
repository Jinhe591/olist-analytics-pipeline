"""
tests/conftest.py
-----------------
Shared pytest fixtures for the Olist pipeline test suite.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Ensure project root is on sys.path for all tests
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(scope="session")
def sample_customers() -> pd.DataFrame:
    """Small representative customers DataFrame."""
    return pd.DataFrame({
        "customer_id":            ["c001", "c002", "c003", "c004"],
        "customer_unique_id":     ["u001", "u002", "u003", "u004"],
        "customer_zip_code_prefix": ["01310", "20040", "30140", "69000"],
        "customer_city":          ["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Manaus"],
        "customer_state":         ["SP", "RJ", "MG", "AM"],
    })


@pytest.fixture(scope="session")
def sample_orders() -> pd.DataFrame:
    """Small representative orders DataFrame with timestamps."""
    return pd.DataFrame({
        "order_id":                      ["o001", "o002", "o003"],
        "customer_id":                   ["c001", "c002", "c003"],
        "order_status":                  ["delivered", "shipped", "canceled"],
        "order_purchase_timestamp":       pd.to_datetime([
            "2018-01-15 10:00:00",
            "2018-03-20 14:30:00",
            "2018-06-01 09:15:00",
        ]),
        "order_approved_at":              pd.to_datetime([
            "2018-01-15 10:05:00",
            "2018-03-20 14:35:00",
            None,
        ]),
        "order_delivered_carrier_date":   pd.to_datetime([
            "2018-01-17 08:00:00",
            None,
            None,
        ]),
        "order_delivered_customer_date":  pd.to_datetime([
            "2018-01-22 15:00:00",
            None,
            None,
        ]),
        "order_estimated_delivery_date":  pd.to_datetime([
            "2018-01-25 00:00:00",
            "2018-04-10 00:00:00",
            "2018-06-20 00:00:00",
        ]),
    })


@pytest.fixture(scope="session")
def sample_products() -> pd.DataFrame:
    """Small representative products DataFrame."""
    return pd.DataFrame({
        "product_id":                    ["p001", "p002", "p003"],
        "product_category_name":         ["beleza_saude", "cama_mesa_banho", None],
        "product_category_name_english": ["health beauty", "bed bath table", "uncategorized"],
        "product_weight_g":              [300.0, 1200.0, None],
        "product_length_cm":             [20.0, 40.0, None],
        "product_height_cm":             [10.0, 15.0, None],
        "product_width_cm":              [15.0, 30.0, None],
    })


@pytest.fixture(scope="session")
def sample_order_items() -> pd.DataFrame:
    """Small representative order items DataFrame."""
    return pd.DataFrame({
        "order_id":      ["o001", "o001", "o002"],
        "order_item_id": [1, 2, 1],
        "product_id":    ["p001", "p002", "p003"],
        "seller_id":     ["s001", "s001", "s002"],
        "price":         [49.90, 89.90, 199.99],
        "freight_value": [5.50,  8.80,  15.00],
    })
