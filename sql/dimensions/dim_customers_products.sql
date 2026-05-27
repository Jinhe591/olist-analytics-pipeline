-- =============================================================
-- dimensions/dim_customers.sql
-- Customer dimension derived from stg_customers.
-- Uses surrogate key + preserved business key.
-- =============================================================

DROP TABLE IF EXISTS dim_customers CASCADE;

CREATE TABLE dim_customers (
    customer_sk             SERIAL        NOT NULL,   -- surrogate key
    customer_id             VARCHAR(50)   NOT NULL,   -- business key
    customer_unique_id      VARCHAR(50)   NOT NULL,
    customer_zip_code_prefix VARCHAR(10),
    customer_city           VARCHAR(100),
    customer_state          CHAR(2),
    CONSTRAINT pk_dim_customers         PRIMARY KEY (customer_sk),
    CONSTRAINT uq_dim_customers_bk      UNIQUE (customer_id)
);

COMMENT ON TABLE dim_customers IS
    'Customer dimension. Grain: one row per customer_id.';
COMMENT ON COLUMN dim_customers.customer_sk         IS 'Surrogate key';
COMMENT ON COLUMN dim_customers.customer_id         IS 'Business key from source system';
COMMENT ON COLUMN dim_customers.customer_unique_id  IS 'Deduplicated customer identifier';

INSERT INTO dim_customers (
    customer_id, customer_unique_id, customer_zip_code_prefix,
    customer_city, customer_state
)
SELECT
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
FROM stg_customers;

CREATE INDEX idx_dim_customers_state ON dim_customers (customer_state);
CREATE INDEX idx_dim_customers_city  ON dim_customers (customer_city);


-- =============================================================
-- dimensions/dim_products.sql
-- Product dimension derived from stg_products.
-- =============================================================

DROP TABLE IF EXISTS dim_products CASCADE;

CREATE TABLE dim_products (
    product_sk                      SERIAL        NOT NULL,   -- surrogate key
    product_id                      VARCHAR(50)   NOT NULL,   -- business key
    product_category_name           VARCHAR(100),
    product_category_name_english   VARCHAR(100),
    product_weight_g                NUMERIC(10,2),
    product_length_cm               NUMERIC(8,2),
    product_height_cm               NUMERIC(8,2),
    product_width_cm                NUMERIC(8,2),
    CONSTRAINT pk_dim_products      PRIMARY KEY (product_sk),
    CONSTRAINT uq_dim_products_bk   UNIQUE (product_id)
);

COMMENT ON TABLE dim_products IS
    'Product dimension. Grain: one row per product_id.';
COMMENT ON COLUMN dim_products.product_sk IS 'Surrogate key';
COMMENT ON COLUMN dim_products.product_id IS 'Business key from source system';

INSERT INTO dim_products (
    product_id, product_category_name, product_category_name_english,
    product_weight_g, product_length_cm, product_height_cm, product_width_cm
)
SELECT
    product_id,
    product_category_name,
    product_category_name_english,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm
FROM stg_products;

CREATE INDEX idx_dim_products_category ON dim_products (product_category_name_english);
