-- =============================================================
-- facts/fact_orders.sql
-- Central fact table for the Olist star schema.
-- Grain: one row per order_id
-- =============================================================

DROP TABLE IF EXISTS fact_orders CASCADE;

CREATE TABLE fact_orders (
    order_sk                        SERIAL        NOT NULL,
    order_id                        VARCHAR(50)   NOT NULL,
    customer_sk                     INTEGER,
    purchase_date_key               INTEGER,
    order_status                    VARCHAR(20),

    -- Revenue measures
    order_revenue                   NUMERIC(12,2),
    order_freight                   NUMERIC(12,2),
    order_total                     NUMERIC(12,2),
    payment_total                   NUMERIC(12,2),
    payment_types                   VARCHAR(100),
    payment_installments            SMALLINT,
    revenue_match_flag              BOOLEAN,

    -- Volume measures
    order_item_count                SMALLINT,
    unique_products                 SMALLINT,
    unique_sellers                  SMALLINT,

    -- Delivery measures
    delivery_duration_days          NUMERIC(6,1),
    is_late_delivery                BOOLEAN,
    suspicious_delivery             BOOLEAN,

    -- Timestamps
    order_purchase_timestamp        TIMESTAMP,
    order_approved_at               TIMESTAMP,
    order_delivered_carrier_date    TIMESTAMP,
    order_delivered_customer_date   TIMESTAMP,
    order_estimated_delivery_date   TIMESTAMP,

    CONSTRAINT pk_fact_orders    PRIMARY KEY (order_sk),
    CONSTRAINT uq_fact_orders_bk UNIQUE (order_id),
    CONSTRAINT fk_fact_customer  FOREIGN KEY (customer_sk)
        REFERENCES dim_customers (customer_sk),
    CONSTRAINT fk_fact_date      FOREIGN KEY (purchase_date_key)
        REFERENCES dim_date (date_key)
);

COMMENT ON TABLE fact_orders IS 'Fact table: one row per order. Grain = order_id.';

-- ── Populate ────────────────────────────────
INSERT INTO fact_orders (
    order_id, customer_sk, purchase_date_key, order_status,
    order_revenue, order_freight, order_total, payment_total,
    payment_types, payment_installments, revenue_match_flag,
    order_item_count, unique_products, unique_sellers,
    delivery_duration_days, is_late_delivery, suspicious_delivery,
    order_purchase_timestamp, order_approved_at,
    order_delivered_carrier_date, order_delivered_customer_date,
    order_estimated_delivery_date
)
SELECT
    orv.order_id,

    -- Surrogate key lookups
    dc.customer_sk,
    CASE
        WHEN o.order_purchase_timestamp IS NOT NULL
        THEN TO_CHAR(o.order_purchase_timestamp::TIMESTAMP, 'YYYYMMDD')::INTEGER
        ELSE NULL
    END,

    o.order_status,

    -- Revenue (already numeric in staging)
    orv.order_revenue::NUMERIC(12,2),
    orv.order_freight::NUMERIC(12,2),
    orv.order_total::NUMERIC(12,2),
    orv.payment_total::NUMERIC(12,2),
    orv.payment_types::VARCHAR(100),
    orv.payment_installments::SMALLINT,

    -- revenue_match_flag: stored as float (1.0/0.0) or text ('True'/'False')
    CASE
        WHEN orv.revenue_match_flag::TEXT IN ('True', 'true', '1', '1.0')  THEN TRUE
        WHEN orv.revenue_match_flag::TEXT IN ('False', 'false', '0', '0.0') THEN FALSE
        ELSE NULL
    END,

    -- Volume
    orv.order_item_count::SMALLINT,
    orv.unique_products::SMALLINT,
    orv.unique_sellers::SMALLINT,

    -- Delivery duration
    o.delivery_duration_days::NUMERIC(6,1),

    -- is_late_delivery: could be boolean, float, or text from CSV
    CASE
        WHEN o.is_late_delivery::TEXT IN ('True', 'true', '1', '1.0')  THEN TRUE
        WHEN o.is_late_delivery::TEXT IN ('False', 'false', '0', '0.0') THEN FALSE
        ELSE NULL
    END,

    -- suspicious_delivery: same handling
    CASE
        WHEN o.suspicious_delivery::TEXT IN ('True', 'true', '1', '1.0')  THEN TRUE
        WHEN o.suspicious_delivery::TEXT IN ('False', 'false', '0', '0.0') THEN FALSE
        ELSE NULL
    END,

    -- Timestamps
    o.order_purchase_timestamp::TIMESTAMP,
    o.order_approved_at::TIMESTAMP,
    o.order_delivered_carrier_date::TIMESTAMP,
    o.order_delivered_customer_date::TIMESTAMP,
    o.order_estimated_delivery_date::TIMESTAMP

FROM stg_order_revenue orv
LEFT JOIN stg_orders    o  ON orv.order_id  = o.order_id
LEFT JOIN dim_customers dc ON o.customer_id = dc.customer_id;

-- ── Indexes ──────────────────────────────────
CREATE INDEX idx_fact_orders_customer_sk       ON fact_orders (customer_sk);
CREATE INDEX idx_fact_orders_purchase_date_key ON fact_orders (purchase_date_key);
CREATE INDEX idx_fact_orders_status            ON fact_orders (order_status);
CREATE INDEX idx_fact_orders_purchase_ts       ON fact_orders (order_purchase_timestamp);


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