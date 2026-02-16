import pandas as pd

#load cleaned datasets
customers = pd.read_csv("data/processed/olist_customers_dataset_clean.csv")
orders = pd.read_csv("data/processed/olist_orders_dataset_clean.csv")
products = pd.read_csv("data/processed/olist_products_dataset_clean.csv")
items = pd.read_csv("data/processed/order_items_clean.csv")
revenue = pd.read_csv("data/processed/order_revenue_enriched.csv")
payments = pd.read_csv("data/processed/payments_clean.csv")
reviews = pd.read_csv("data/processed/reviews_clean.csv")
sellers = pd.read_csv("data/processed/sellers_clean.csv")

print("\nNull checks\n")

datasets = {
    "customers": customers,
    "orders": orders,
    "products": products,
    "items": items,
    "revenue": revenue,
    "payments": payments,
    "reviews": reviews,
    "sellers": sellers,
}

for name, df in datasets.items():
    print(name)
    print(df.isnull().sum())
    print()

print("Duplicate checks\n")

for name, df in datasets.items():
    print(name, "duplicates:", df.duplicated().sum())

print("\nRevenue validation\n")

items["items_total"] = items["price"] + items["freight_value"]

items_total = items.groupby("order_id")["items_total"].sum().reset_index()
payments_total = payments.groupby("order_id")["payment_value"].sum().reset_index()

comparison = items_total.merge(payments_total, on="order_id")

comparison["difference"] = (
    comparison["items_total"] - comparison["payment_value"]
).abs()

matching_orders = (comparison["difference"] < 0.01).sum()
total_orders = len(comparison)

print("matching orders:", matching_orders)
print("total orders:", total_orders)
print("match percentage:", round((matching_orders / total_orders) * 100, 2), "%")

print("\nDelivery validation\n")

orders["order_delivered_customer_date"] = pd.to_datetime(
    orders["order_delivered_customer_date"], errors="coerce"
)

orders["order_estimated_delivery_date"] = pd.to_datetime(
    orders["order_estimated_delivery_date"], errors="coerce"
)

total_orders = len(orders)
delivered = orders["order_delivered_customer_date"].notna().sum()
not_delivered = total_orders - delivered

orders["delay_days"] = (
    orders["order_delivered_customer_date"]
    - orders["order_estimated_delivery_date"]
).dt.days

late_deliveries = (orders["delay_days"] > 0).sum()

print("total orders:", total_orders)
print("delivered:", delivered)
print("not delivered:", not_delivered)
print("late deliveries:", late_deliveries)