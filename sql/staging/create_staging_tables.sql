-- =============================================================
-- staging/create_staging_tables.sql
-- Creates all staging tables for the Olist analytics pipeline.
-- Idempotent: safe to run multiple times.
-- =============================================================

-- ─────────────────────────────────────────────
-- stg_customers
-- ─────────────────────────────────────────────
DROP TABLE IF EXISTS stg_customers CASCADE;

CREATE TABLE stg_customers (
    customer_id             VARCHAR(50)  NOT NULL,
    customer_unique_id      VARCHAR(50)  NOT NULL,
    customer_zip_code_prefix VARCHAR(10),
    customer_city           VARCHAR(100),
    customer_state          CHAR(2),
    CONSTRAINT pk_stg_customers PRIMARY KEY (customer_id)
);

COMMENT ON TABLE stg_customers IS
    'Staging: one row per customer_id from olist_customers_dataset.csv';

-- ─────────────────────────────────────────────
-- stg_products
-- ─────────────────────────────────────────────
DROP TABLE IF EXISTS stg_products CASCADE;

CREATE TABLE stg_products (
    product_id                      VARCHAR(50)  NOT NULL,
    product_category_name           VARCHAR(100),
    product_category_name_english   VARCHAR(100),
    product_name_lenght             SMALLINT,
    product_description_lenght      INTEGER,
    product_photos_qty              SMALLINT,
    product_weight_g                NUMERIC(10,2),
    product_length_cm               NUMERIC(8,2),
    product_height_cm               NUMERIC(8,2),
    product_width_cm                NUMERIC(8,2),
    CONSTRAINT pk_stg_products PRIMARY KEY (product_id)
);

COMMENT ON TABLE stg_products IS
    'Staging: one row per product_id with English category names.';

-- ─────────────────────────────────────────────
-- stg_orders
-- ─────────────────────────────────────────────
DROP TABLE IF EXISTS stg_orders CASCADE;

CREATE TABLE stg_orders (
    order_id                        VARCHAR(50)  NOT NULL,
    customer_id                     VARCHAR(50)  NOT NULL,
    order_status                    VARCHAR(20),
    order_purchase_timestamp        TIMESTAMP,
    order_approved_at               TIMESTAMP,
    order_delivered_carrier_date    TIMESTAMP,
    order_delivered_customer_date   TIMESTAMP,
    order_estimated_delivery_date   TIMESTAMP,
    delivery_duration_days          NUMERIC(6,1),
    is_late_delivery                BOOLEAN,
    suspicious_delivery             BOOLEAN,
    CONSTRAINT pk_stg_orders PRIMARY KEY (order_id)
);

COMMENT ON TABLE stg_orders IS
    'Staging: one row per order_id. Includes derived delivery metrics.';

-- ─────────────────────────────────────────────
-- stg_order_revenue
-- ─────────────────────────────────────────────
DROP TABLE IF EXISTS stg_order_revenue CASCADE;

CREATE TABLE stg_order_revenue (
    order_id                VARCHAR(50)  NOT NULL,
    order_revenue           NUMERIC(12,2),
    order_freight           NUMERIC(12,2),
    order_total             NUMERIC(12,2),
    order_item_count        SMALLINT,
    unique_products         SMALLINT,
    unique_sellers          SMALLINT,
    payment_total           NUMERIC(12,2),
    payment_types           VARCHAR(100),
    payment_installments    SMALLINT,
    revenue_match_flag      BOOLEAN,
    customer_id             VARCHAR(50),
    order_status            VARCHAR(20),
    order_purchase_timestamp TIMESTAMP,
    CONSTRAINT pk_stg_order_revenue PRIMARY KEY (order_id)
);

COMMENT ON TABLE stg_order_revenue IS
    'Staging: order-level revenue aggregates with payment reconciliation.';
