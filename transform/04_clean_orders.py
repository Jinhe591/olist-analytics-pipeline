import pandas as pd

df = pd.read_csv("data/raw/olist_orders_dataset.csv")

#convert dates
date_cols = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]

for col in date_cols:
    df[col] = pd.to_datetime(df[col], errors="coerce")

#delivery delay feature
df["delivery_delay_days"] = (
    df["order_delivered_customer_date"]
    - df["order_estimated_delivery_date"]
).dt.days

df = df.drop_duplicates()

df.to_csv("data/processed/orders_clean.csv", index=False)

print("Saved orders_clean")