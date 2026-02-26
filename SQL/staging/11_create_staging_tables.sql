-- Create database
CREATE DATABASE IF NOT EXISTS olist_warehouse;
USE olist_warehouse;


-- stg_customers
CREATE TABLE stg_customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_unique_id VARCHAR(50),
    customer_zip_code_prefix VARCHAR(10),
    customer_city VARCHAR(100),
    customer_state CHAR(2),
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- stg_orders
CREATE TABLE stg_orders (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    order_status VARCHAR(50),
    order_purchase_timestamp DATETIME,
    order_approved_at DATETIME,
    order_delivered_carrier_date DATETIME,
    order_delivered_customer_date DATETIME,
    order_estimated_delivery_date DATETIME,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id)
        REFERENCES stg_customers(customer_id)
);


-- stg_products
CREATE TABLE stg_products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_category_name VARCHAR(100),
    product_name_length INT,
    product_description_length INT,
    product_photos_qty INT,
    product_weight_g INT,
    product_length_cm INT,
    product_height_cm INT,
    product_width_cm INT,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- stg_sellers
CREATE TABLE stg_sellers (
    seller_id VARCHAR(50) PRIMARY KEY,
    seller_zip_code_prefix VARCHAR(10),
    seller_city VARCHAR(100),
    seller_state CHAR(2),
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- stg_order_items
CREATE TABLE stg_order_items (
    order_id VARCHAR(50),
    order_item_id INT,
    product_id VARCHAR(50),
    seller_id VARCHAR(50),
    shipping_limit_date DATETIME,
    price DECIMAL(10,2),
    freight_value DECIMAL(10,2),
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (order_id, order_item_id, product_id, seller_id),
    FOREIGN KEY (order_id) REFERENCES stg_orders(order_id),
    FOREIGN KEY (product_id) REFERENCES stg_products(product_id),
    FOREIGN KEY (seller_id) REFERENCES stg_sellers(seller_id)
);


-- stg_order_revenue_enriched
CREATE TABLE stg_order_revenue_enriched (
    order_id VARCHAR(50),
    product_id VARCHAR(50),
    seller_id VARCHAR(50),
    order_item_id INT,
    price DECIMAL(10,2),
    freight_value DECIMAL(10,2),
    total_revenue DECIMAL(10,2),
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (order_id, product_id, seller_id, order_item_id)
);


-- stg_payments
CREATE TABLE stg_payments (
    order_id VARCHAR(50),
    payment_sequential INT,
    payment_type VARCHAR(50),
    payment_installments INT,
    payment_value DECIMAL(10,2),
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (order_id, payment_sequential),
    FOREIGN KEY (order_id) REFERENCES stg_orders(order_id)
);


-- stg_reviews
CREATE TABLE stg_reviews (
    review_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50),
    review_score INT,
    review_comment_title VARCHAR(255),
    review_comment_message TEXT,
    review_creation_date DATETIME,
    review_answer_timestamp DATETIME,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES stg_orders(order_id)
);