-- =============================================================
-- views/seller_performance_views.sql
-- Seller-focused analytical views.
-- Uses public. schema prefix to avoid search path issues.
-- =============================================================

-- ─────────────────────────────────────────────
-- vw_seller_performance
-- ─────────────────────────────────────────────
DROP VIEW IF EXISTS vw_seller_performance CASCADE;

CREATE OR REPLACE VIEW vw_seller_performance AS
SELECT
    ds.seller_id,
    ds.seller_city,
    ds.seller_state,
    COUNT(DISTINCT foi.order_id)                AS total_orders,
    COUNT(foi.item_sk)                          AS total_items_sold,
    ROUND(SUM(foi.price)::NUMERIC, 2)           AS total_revenue,
    ROUND(AVG(foi.price)::NUMERIC, 2)           AS avg_item_price,
    ROUND(SUM(foi.freight_value)::NUMERIC, 2)   AS total_freight_collected,
    COUNT(DISTINCT dp.product_category_name_english) AS unique_categories,
    ROUND(
        100.0 * SUM(fo.is_late_delivery::INT)
            / NULLIF(SUM(CASE WHEN fo.is_late_delivery IS NOT NULL THEN 1 END), 0), 2
    )                                           AS seller_late_delivery_pct
FROM public.fact_order_items foi
JOIN public.dim_sellers  ds ON foi.seller_sk  = ds.seller_sk
JOIN public.dim_products dp ON foi.product_sk = dp.product_sk
JOIN public.fact_orders  fo ON foi.order_sk   = fo.order_sk
WHERE fo.order_status NOT IN ('canceled', 'unavailable')
GROUP BY ds.seller_id, ds.seller_city, ds.seller_state
ORDER BY total_revenue DESC;

COMMENT ON VIEW vw_seller_performance IS
    'Seller-level revenue, volume, and delivery performance metrics.';


-- ─────────────────────────────────────────────
-- vw_top_products
-- ─────────────────────────────────────────────
DROP VIEW IF EXISTS vw_top_products CASCADE;

CREATE OR REPLACE VIEW vw_top_products AS
SELECT
    dp.product_id,
    dp.product_category_name_english            AS category,
    COUNT(DISTINCT foi.order_id)                AS total_orders,
    COUNT(foi.item_sk)                          AS units_sold,
    ROUND(SUM(foi.price)::NUMERIC, 2)           AS total_revenue,
    ROUND(AVG(foi.price)::NUMERIC, 2)           AS avg_price,
    RANK() OVER (ORDER BY SUM(foi.price) DESC)  AS revenue_rank
FROM public.fact_order_items foi
JOIN public.dim_products dp ON foi.product_sk = dp.product_sk
JOIN public.fact_orders  fo ON foi.order_sk   = fo.order_sk
WHERE fo.order_status NOT IN ('canceled', 'unavailable')
GROUP BY dp.product_id, dp.product_category_name_english
ORDER BY total_revenue DESC
LIMIT 50;

COMMENT ON VIEW vw_top_products IS
    'Top 50 products ranked by gross revenue.';


-- ─────────────────────────────────────────────
-- vw_payment_analysis
-- ─────────────────────────────────────────────
DROP VIEW IF EXISTS vw_payment_analysis CASCADE;

CREATE OR REPLACE VIEW vw_payment_analysis AS
WITH payment_types_exploded AS (
    SELECT
        fo.order_sk,
        fo.order_revenue,
        fo.payment_installments,
        fo.purchase_date_key,
        TRIM(unnested.type) AS payment_type
    FROM public.fact_orders fo,
         LATERAL UNNEST(STRING_TO_ARRAY(fo.payment_types, '|')) AS unnested(type)
    WHERE fo.order_status NOT IN ('canceled', 'unavailable')
)
SELECT
    payment_type,
    COUNT(DISTINCT order_sk)                        AS total_orders,
    ROUND(SUM(order_revenue)::NUMERIC, 2)           AS total_revenue,
    ROUND(AVG(order_revenue)::NUMERIC, 2)           AS avg_order_value,
    ROUND(AVG(payment_installments)::NUMERIC, 1)    AS avg_installments,
    ROUND(
        100.0 * COUNT(DISTINCT order_sk)
            / SUM(COUNT(DISTINCT order_sk)) OVER (), 2
    )                                               AS pct_of_orders
FROM payment_types_exploded
GROUP BY payment_type
ORDER BY total_orders DESC;

COMMENT ON VIEW vw_payment_analysis IS
    'Payment method distribution.';


-- ─────────────────────────────────────────────
-- vw_order_status_summary
-- ─────────────────────────────────────────────
DROP VIEW IF EXISTS vw_order_status_summary CASCADE;

CREATE OR REPLACE VIEW vw_order_status_summary AS
SELECT
    order_status,
    COUNT(order_id)                             AS order_count,
    ROUND(
        100.0 * COUNT(order_id)
            / SUM(COUNT(order_id)) OVER (), 2
    )                                           AS pct_of_all_orders,
    ROUND(COALESCE(SUM(order_revenue), 0)::NUMERIC, 2) AS total_revenue
FROM public.fact_orders
GROUP BY order_status
ORDER BY order_count DESC;

COMMENT ON VIEW vw_order_status_summary IS
    'Order funnel breakdown by status.';