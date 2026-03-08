import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path

# -----------------------------------
# CONFIG
# -----------------------------------

DATA_PATH = Path("data/processed")
DB_PATH = "sqlite:///olist_warehouse.db"

engine = create_engine(DB_PATH)

# -----------------------------------
# LOAD DATA
# -----------------------------------

print("Loading CSV files...")

customers = pd.read_csv(DATA_PATH / "olist_customers_dataset_clean.csv")
orders = pd.read_csv(DATA_PATH / "olist_orders_dataset_clean.csv")
products = pd.read_csv(DATA_PATH / "olist_products_dataset_clean.csv")
order_items = pd.read_csv(DATA_PATH / "order_items_clean.csv")
payments = pd.read_csv(DATA_PATH / "payments_clean.csv")
reviews = pd.read_csv(DATA_PATH / "reviews_clean.csv")
sellers = pd.read_csv(DATA_PATH / "sellers_clean.csv")

# -----------------------------------
# CREATE STAGING TABLES
# -----------------------------------

print("Creating staging tables...")

customers.to_sql("stg_customers", engine, if_exists="replace", index=False)
orders.to_sql("stg_orders", engine, if_exists="replace", index=False)
products.to_sql("stg_products", engine, if_exists="replace", index=False)
order_items.to_sql("stg_order_items", engine, if_exists="replace", index=False)
payments.to_sql("stg_payments", engine, if_exists="replace", index=False)
reviews.to_sql("stg_reviews", engine, if_exists="replace", index=False)
sellers.to_sql("stg_sellers", engine, if_exists="replace", index=False)

print("Staging tables created.")

# -----------------------------------
# STAR SCHEMA
# -----------------------------------

with engine.begin() as conn:

    print("Creating dimension tables...")

    conn.execute(text("DROP TABLE IF EXISTS dim_customers"))
    conn.execute(text("DROP TABLE IF EXISTS dim_products"))
    conn.execute(text("DROP TABLE IF EXISTS dim_date"))
    conn.execute(text("DROP TABLE IF EXISTS fact_orders"))

    conn.execute(text("""
    CREATE TABLE dim_customers AS
    SELECT
        ROW_NUMBER() OVER () AS customer_key,
        customer_id,
        customer_unique_id,
        customer_city,
        customer_state
    FROM stg_customers
    """))

    conn.execute(text("""
    CREATE TABLE dim_products AS
    SELECT
        ROW_NUMBER() OVER () AS product_key,
        product_id,
        product_category_name,
        product_weight_g
    FROM stg_products
    """))

    conn.execute(text("""
    CREATE TABLE dim_date AS
    SELECT DISTINCT
        strftime('%Y%m%d', order_purchase_timestamp) AS date_key,
        date(order_purchase_timestamp) AS full_date,
        strftime('%Y', order_purchase_timestamp) AS year,
        strftime('%m', order_purchase_timestamp) AS month,
        strftime('%d', order_purchase_timestamp) AS day
    FROM stg_orders
    """))

    print("Creating fact table...")

    conn.execute(text("""
    CREATE TABLE fact_orders AS
    SELECT
        oi.order_id,
        dc.customer_key,
        dp.product_key,
        strftime('%Y%m%d', o.order_purchase_timestamp) AS date_key,
        oi.price,
        oi.freight_value,
        (oi.price + oi.freight_value) AS total_revenue
    FROM stg_order_items oi
    JOIN stg_orders o
        ON oi.order_id = o.order_id
    JOIN dim_customers dc
        ON o.customer_id = dc.customer_id
    JOIN dim_products dp
        ON oi.product_id = dp.product_id
    """))

print("Star schema created.")

# -----------------------------------
# VALIDATION
# -----------------------------------

with engine.connect() as conn:

    print("\nRunning validations...")

    staging_revenue = conn.execute(text("""
    SELECT SUM(price + freight_value)
    FROM stg_order_items
    """)).scalar()

    warehouse_revenue = conn.execute(text("""
    SELECT SUM(total_revenue)
    FROM fact_orders
    """)).scalar()

    order_count = conn.execute(text("""
    SELECT COUNT(DISTINCT order_id)
    FROM fact_orders
    """)).scalar()

print("\nValidation Results")
print("Staging Revenue:", staging_revenue)
print("Warehouse Revenue:", warehouse_revenue)
print("Total Orders:", order_count)

print("\nWarehouse build complete.")