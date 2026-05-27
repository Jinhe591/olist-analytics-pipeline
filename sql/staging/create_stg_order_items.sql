-- =============================================================
-- staging/create_stg_order_items.sql
--
-- Staging table for order items — required by vw_revenue_by_category.
-- Loaded directly from data/raw/olist_order_items_dataset.csv.
-- =============================================================

DROP TABLE IF EXISTS stg_order_items CASCADE;

CREATE TABLE stg_order_items (
    order_id            VARCHAR(50)   NOT NULL,
    order_item_id       SMALLINT      NOT NULL,
    product_id          VARCHAR(50),
    seller_id           VARCHAR(50),
    shipping_limit_date TIMESTAMP,
    price               NUMERIC(10,2),
    freight_value       NUMERIC(10,2),
    CONSTRAINT pk_stg_order_items PRIMARY KEY (order_id, order_item_id)
);

COMMENT ON TABLE stg_order_items IS
    'Staging: one row per order line item. Grain = (order_id, order_item_id).';

CREATE INDEX idx_stg_order_items_product ON stg_order_items (product_id);
CREATE INDEX idx_stg_order_items_order   ON stg_order_items (order_id);
