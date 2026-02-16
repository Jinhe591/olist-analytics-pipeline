import pandas as pd

df = pd.read_csv("data/raw/olist_sellers_dataset.csv")

df["seller_city"] = df["seller_city"].str.lower().str.strip()
df["seller_state"] = df["seller_state"].str.upper().str.strip()

df = df.drop_duplicates()

df.to_csv("data/processed/sellers_clean.csv", index=False)

print("Saved sellers_clean")