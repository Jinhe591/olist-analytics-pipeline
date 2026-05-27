-- =============================================================
-- views/business_views.sql
--
-- Analytical views encapsulating common KPI calculations.
-- These power the Power BI semantic model.
-- =============================================================


-- ─────────────────────────────────────────────
-- vw_monthly_revenue
-- Monthly revenue trend for the sales overview dashboard.
-- ─────────────────────────────────────────────

CREATE OR REPLACE VIEW vw_monthly_revenue AS
SELECT
    dd.year,
    dd.month,
    dd.month_name_short,
    dd.year_month,
    COUNT(fo.order_id)                          AS total_orders,
    ROUND(SUM(fo.order_revenue)::NUMERIC, 2)    AS total_revenue,
    ROUND(SUM(fo.order_freight)::NUMERIC, 2)    AS total_freight,
    ROUND(SUM(fo.order_total)::NUMERIC, 2)      AS total_order_value,
    ROUND(AVG(fo.order_revenue)::NUMERIC, 2)    AS avg_order_value,
    COUNT(DISTINCT fo.customer_sk)              AS unique_customers
FROM fact_orders fo
JOIN dim_date dd ON fo.purchase_date_key = dd.date_key
WHERE fo.order_status NOT IN ('canceled', 'unavailable')
GROUP BY dd.year, dd.month, dd.month_name_short, dd.year_month
ORDER BY dd.year, dd.month;

COMMENT ON VIEW vw_monthly_revenue IS
    'Monthly revenue KPIs excluding canceled/unavailable orders.';


-- ─────────────────────────────────────────────
-- vw_revenue_by_category
-- Product category performance.
-- ─────────────────────────────────────────────

CREATE OR REPLACE VIEW vw_revenue_by_category AS
SELECT
    COALESCE(dp.product_category_name_english, 'unknown') AS category,
    COUNT(DISTINCT fo.order_id)                           AS total_orders,
    SUM(oi.price)                                         AS total_revenue,
    ROUND(AVG(oi.price)::NUMERIC, 2)                      AS avg_item_price,
    COUNT(oi.order_item_id)                               AS total_items_sold,
    COUNT(DISTINCT dp.product_id)                         AS unique_products
FROM stg_order_items oi                  -- item-level grain for accuracy
JOIN stg_orders so      ON oi.order_id   = so.order_id
JOIN dim_products dp    ON oi.product_id = dp.product_id
JOIN fact_orders fo     ON oi.order_id   = fo.order_id
WHERE so.order_status NOT IN ('canceled', 'unavailable')
GROUP BY COALESCE(dp.product_category_name_english, 'unknown')
ORDER BY total_revenue DESC;

COMMENT ON VIEW vw_revenue_by_category IS
    'Revenue and order volume aggregated by product category.';


-- ─────────────────────────────────────────────
-- vw_revenue_by_state
-- Geographic revenue breakdown.
-- ─────────────────────────────────────────────

CREATE OR REPLACE VIEW vw_revenue_by_state AS
SELECT
    COALESCE(dc.customer_state, 'XX')           AS state,
    COUNT(DISTINCT fo.order_id)                 AS total_orders,
    COUNT(DISTINCT fo.customer_sk)              AS unique_customers,
    ROUND(SUM(fo.order_revenue)::NUMERIC, 2)    AS total_revenue,
    ROUND(AVG(fo.order_revenue)::NUMERIC, 2)    AS avg_order_value,
    ROUND(
        100.0 * COALESCE(SUM(fo.is_late_delivery::INT), 0)
            / NULLIF(COUNT(fo.is_late_delivery), 0), 2
    )                                           AS late_delivery_pct
FROM fact_orders fo
JOIN dim_customers dc ON fo.customer_sk = dc.customer_sk
WHERE fo.order_status NOT IN ('canceled', 'unavailable')
GROUP BY COALESCE(dc.customer_state, 'XX')
ORDER BY total_revenue DESC;

COMMENT ON VIEW vw_revenue_by_state IS
    'Revenue, orders, and delivery performance by Brazilian state.';


-- ─────────────────────────────────────────────
-- vw_delivery_performance
-- Delivery KPIs over time.
-- ─────────────────────────────────────────────

CREATE OR REPLACE VIEW vw_delivery_performance AS
SELECT
    dd.year,
    dd.month,
    dd.year_month,
    COUNT(fo.order_id)                                      AS delivered_orders,
    ROUND(AVG(fo.delivery_duration_days)::NUMERIC, 1)       AS avg_delivery_days,
    SUM(fo.is_late_delivery::INT)                           AS late_deliveries,
    COUNT(fo.is_late_delivery)                              AS total_with_delivery_data,
    ROUND(
        100.0 * SUM(fo.is_late_delivery::INT)
            / NULLIF(COUNT(fo.is_late_delivery), 0), 2
    )                                                       AS late_pct,
    ROUND(
        100.0 * (COUNT(fo.is_late_delivery) - SUM(fo.is_late_delivery::INT))
            / NULLIF(COUNT(fo.is_late_delivery), 0), 2
    )                                                       AS on_time_pct
FROM fact_orders fo
JOIN dim_date dd ON fo.purchase_date_key = dd.date_key
WHERE fo.order_status = 'delivered'
  AND fo.is_late_delivery IS NOT NULL
GROUP BY dd.year, dd.month, dd.year_month
ORDER BY dd.year, dd.month;

COMMENT ON VIEW vw_delivery_performance IS
    'Monthly delivery performance: on-time vs late rates and average duration.';


-- ─────────────────────────────────────────────
-- vw_customer_kpis
-- Customer-level revenue summary.
-- ─────────────────────────────────────────────

CREATE OR REPLACE VIEW vw_customer_kpis AS
SELECT
    dc.customer_unique_id,
    dc.customer_state,
    dc.customer_city,
    COUNT(fo.order_id)                          AS total_orders,
    ROUND(SUM(fo.order_revenue)::NUMERIC, 2)    AS total_revenue,
    ROUND(AVG(fo.order_revenue)::NUMERIC, 2)    AS avg_order_value,
    MIN(fo.order_purchase_timestamp)            AS first_order_date,
    MAX(fo.order_purchase_timestamp)            AS last_order_date,
    CASE
        WHEN COUNT(fo.order_id) = 1 THEN 'One-Time'
        WHEN COUNT(fo.order_id) BETWEEN 2 AND 4 THEN 'Repeat'
        ELSE 'Loyal'
    END                                         AS customer_segment
FROM fact_orders fo
JOIN dim_customers dc ON fo.customer_sk = dc.customer_sk
WHERE fo.order_status NOT IN ('canceled', 'unavailable')
GROUP BY dc.customer_unique_id, dc.customer_state, dc.customer_city;

COMMENT ON VIEW vw_customer_kpis IS
    'Per-customer revenue KPIs with simple segmentation.';
