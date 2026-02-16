import pandas as pd

#load
df = pd.read_csv("data/raw/olist_customers_dataset.csv")

#clean
df["customer_city"] = df["customer_city"].str.lower().str.strip()
df["customer_state"] = df["customer_state"].str.upper().str.strip()

#remove duplicates (safety)
df = df.drop_duplicates()

#save
df.to_csv("data/processed/customers_clean.csv", index=False)

print("Saved customers_clean")