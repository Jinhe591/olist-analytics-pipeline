import pandas as pd
import mysql.connector
from pathlib import Path

#CONNECTION
connection = mysql.connector.connect(
    host="Hadi",
    user="root",
    password="Malgus12",
    database="olist_warehouse"
)

cursor = connection.cursor()

BASE_PATH = Path("data/processed")

#HELPER FUNCTION
def load_csv_to_table(csv_file, table_name):
    print(f"Loading {csv_file} → {table_name}")

    df = pd.read_csv(BASE_PATH / csv_file)

    cols = ",".join(df.columns)
    placeholders = ",".join(["%s"] * len(df.columns))

    sql = f"""
        INSERT INTO {table_name} ({cols})
        VALUES ({placeholders})
    """

    data = [tuple(x) for x in df.to_numpy()]

    cursor.executemany(sql, data)
    connection.commit()

    print(f"✅ {table_name} loaded")



# LOAD TABLES

load_csv_to_table(
    "olist_customers_dataset_clean.csv",
    "stg_customers"
)

load_csv_to_table(
    "olist_orders_dataset_clean.csv",
    "stg_orders"
)

load_csv_to_table(
    "olist_products_dataset_clean.csv",
    "stg_products"
)

load_csv_to_table(
    "sellers_clean.csv",
    "stg_sellers"
)

load_csv_to_table(
    "order_items_clean.csv",
    "stg_order_items"
)

load_csv_to_table(
    "order_revenue_enriched.csv",
    "stg_order_revenue_enriched"
)

load_csv_to_table(
    "payments_clean.csv",
    "stg_payments"
)

load_csv_to_table(
    "reviews_clean.csv",
    "stg_reviews"
)

cursor.close()
connection.close()

print("All staging tables loaded")