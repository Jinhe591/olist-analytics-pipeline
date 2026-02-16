import pandas as pd

items = pd.read_csv("data/processed/order_items_clean.csv")
payments = pd.read_csv("data/processed/payments_clean.csv")

#revenue per order from items
revenue = (
    items.groupby("order_id")["total_price"]
    .sum()
    .reset_index()
)

revenue.rename(columns={"total_price": "order_revenue"}, inplace=True)

#merge payment info
final = revenue.merge(payments, on="order_id", how="left")

final.to_csv("data/processed/order_revenue_enriched.csv", index=False)

print("Saved order_revenue_enriched")