import pandas as pd

df = pd.read_csv("data/raw/olist_products_dataset.csv")

#fill missing category
df["product_category_name"] = df["product_category_name"].fillna("unknown")

#numeric columns fill with median
num_cols = [
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
]

for col in num_cols:
    df[col] = df[col].fillna(df[col].median())

df = df.drop_duplicates()

df.to_csv("data/processed/products_clean.csv", index=False)

print("Saved products_clean")