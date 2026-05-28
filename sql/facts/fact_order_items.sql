-- =============================================================
-- facts/fact_order_items.sql
-- Item-grain fact table.
-- =============================================================

DROP TABLE IF EXISTS public.fact_order_items CASCADE;

CREATE TABLE public.fact_order_items (
    item_sk             SERIAL        NOT NULL,
    order_id            VARCHAR(50)   NOT NULL,
    order_item_id       SMALLINT      NOT NULL,
    order_sk            INTEGER,
    product_sk          INTEGER,
    seller_sk           INTEGER,
    customer_sk         INTEGER,
    purchase_date_key   INTEGER,
    price               NUMERIC(10,2),
    freight_value       NUMERIC(10,2),
    total_item_value    NUMERIC(10,2),
    shipping_limit_date TIMESTAMP,

    CONSTRAINT pk_fact_order_items  PRIMARY KEY (item_sk),
    CONSTRAINT uq_fact_item_bk      UNIQUE (order_id, order_item_id),
    CONSTRAINT fk_item_order        FOREIGN KEY (order_sk)
        REFERENCES public.fact_orders (order_sk),
    CONSTRAINT fk_item_product      FOREIGN KEY (product_sk)
        REFERENCES public.dim_products (product_sk),
    CONSTRAINT fk_item_seller       FOREIGN KEY (seller_sk)
        REFERENCES public.dim_sellers (seller_sk),
    CONSTRAINT fk_item_customer     FOREIGN KEY (customer_sk)
        REFERENCES public.dim_customers (customer_sk),
    CONSTRAINT fk_item_date         FOREIGN KEY (purchase_date_key)
        REFERENCES public.dim_date (date_key)
);

COMMENT ON TABLE public.fact_order_items IS
    'Item-grain fact table. One row per order line item.';

INSERT INTO public.fact_order_items (
    order_id, order_item_id, order_sk, product_sk, seller_sk,
    customer_sk, purchase_date_key, price, freight_value,
    total_item_value, shipping_limit_date
)
SELECT
    oi.order_id,
    oi.order_item_id::SMALLINT,
    fo.order_sk,
    dp.product_sk,
    ds.seller_sk,
    fo.customer_sk,
    fo.purchase_date_key,
    oi.price::NUMERIC(10,2),
    oi.freight_value::NUMERIC(10,2),
    (COALESCE(oi.price, 0) + COALESCE(oi.freight_value, 0))::NUMERIC(10,2),
    oi.shipping_limit_date::TIMESTAMP
FROM public.stg_order_items oi
LEFT JOIN public.fact_orders   fo ON oi.order_id   = fo.order_id
LEFT JOIN public.dim_products  dp ON oi.product_id = dp.product_id
LEFT JOIN public.dim_sellers   ds ON oi.seller_id  = ds.seller_id;

CREATE INDEX idx_foi_order_sk          ON public.fact_order_items (order_sk);
CREATE INDEX idx_foi_product_sk        ON public.fact_order_items (product_sk);
CREATE INDEX idx_foi_seller_sk         ON public.fact_order_items (seller_sk);
CREATE INDEX idx_foi_purchase_date_key ON public.fact_order_items (purchase_date_key);