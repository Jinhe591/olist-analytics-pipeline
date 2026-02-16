import pandas as pd

df = pd.read_csv("data/raw/olist_order_items_dataset.csv")

df["shipping_limit_date"] = pd.to_datetime(
    df["shipping_limit_date"], errors="coerce"
)

# total item value
df["total_price"] = df["price"] + df["freight_value"]

df = df.drop_duplicates()

df.to_csv("data/processed/order_items_clean.csv", index=False)

print("Saved order_items_clean")