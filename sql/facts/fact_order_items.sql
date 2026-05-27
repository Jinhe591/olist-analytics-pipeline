-- =============================================================
-- facts/fact_order_items.sql
--
-- Item-grain fact table for product-level analysis.
-- Complements fact_orders (order grain) in the star schema.
--
-- Grain
-- -----
-- One row per order line item: (order_id, order_item_id)
--
-- Use this table for:
--   - Revenue by product / category
--   - Seller performance
--   - Basket analysis
-- =============================================================

DROP TABLE IF EXISTS fact_order_items CASCADE;

CREATE TABLE fact_order_items (
    item_sk             INTEGER       NOT NULL GENERATED ALWAYS AS IDENTITY,
    order_id            VARCHAR(50)   NOT NULL,   -- degenerate dim (BK)
    order_item_id       SMALLINT      NOT NULL,
    order_sk            INTEGER,                  -- FK → fact_orders
    product_sk          INTEGER,                  -- FK → dim_products
    seller_sk           INTEGER,                  -- FK → dim_sellers
    customer_sk         INTEGER,                  -- FK → dim_customers (via order)
    purchase_date_key   INTEGER,                  -- FK → dim_date

    -- ── Price measures ──────────────────
    price               NUMERIC(10,2),
    freight_value       NUMERIC(10,2),
    total_item_value    NUMERIC(10,2)
        GENERATED ALWAYS AS (price + freight_value) STORED,

    -- ── Timestamp (degenerate) ──────────
    shipping_limit_date TIMESTAMP,

    CONSTRAINT pk_fact_order_items  PRIMARY KEY (item_sk),
    CONSTRAINT uq_fact_item_bk      UNIQUE (order_id, order_item_id),
    CONSTRAINT fk_item_order        FOREIGN KEY (order_sk)
        REFERENCES fact_orders (order_sk),
    CONSTRAINT fk_item_product      FOREIGN KEY (product_sk)
        REFERENCES dim_products (product_sk),
    CONSTRAINT fk_item_seller       FOREIGN KEY (seller_sk)
        REFERENCES dim_sellers (seller_sk),
    CONSTRAINT fk_item_customer     FOREIGN KEY (customer_sk)
        REFERENCES dim_customers (customer_sk),
    CONSTRAINT fk_item_date         FOREIGN KEY (purchase_date_key)
        REFERENCES dim_date (date_key)
);

COMMENT ON TABLE fact_order_items IS
    'Item-grain fact table. One row per order line item.
     Join to fact_orders for order-level context.';

-- ── Populate ────────────────────────────────
INSERT INTO fact_order_items (
    order_id, order_item_id, order_sk, product_sk, seller_sk,
    customer_sk, purchase_date_key, price, freight_value, shipping_limit_date
)
SELECT
    oi.order_id,
    oi.order_item_id,

    fo.order_sk,
    dp.product_sk,
    ds.seller_sk,
    fo.customer_sk,
    fo.purchase_date_key,

    oi.price,
    oi.freight_value,
    oi.shipping_limit_date
FROM stg_order_items oi
LEFT JOIN fact_orders   fo ON oi.order_id   = fo.order_id
LEFT JOIN dim_products  dp ON oi.product_id = dp.product_id
LEFT JOIN dim_sellers   ds ON oi.seller_id  = ds.seller_id;

-- ── Indexes ─────────────────────────────────
CREATE INDEX idx_foi_order_sk          ON fact_order_items (order_sk);
CREATE INDEX idx_foi_product_sk        ON fact_order_items (product_sk);
CREATE INDEX idx_foi_seller_sk         ON fact_order_items (seller_sk);
CREATE INDEX idx_foi_purchase_date_key ON fact_order_items (purchase_date_key);
