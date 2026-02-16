import pandas as pd

df = pd.read_csv("data/raw/olist_order_payments_dataset.csv")

#standardize payment type
df["payment_type"] = df["payment_type"].str.lower().str.strip()

df = df.drop_duplicates()

df.to_csv("data/processed/payments_clean.csv", index=False)

print("Saved payments_clean")