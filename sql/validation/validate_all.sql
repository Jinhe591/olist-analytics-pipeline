-- =============================================================
-- validation/validate_all.sql
--
-- Data integrity validation suite for the Olist star schema.
-- Each query should return 0 rows (or 0 count) if data is valid.
-- =============================================================


-- ─────────────────────────────────────────────
-- 1. Primary Key Uniqueness Checks
-- ─────────────────────────────────────────────

-- [1a] Duplicate order_id in fact_orders
SELECT 'FAIL: duplicate order_id in fact_orders' AS check_name, COUNT(*) AS violations
FROM (
    SELECT order_id, COUNT(*) AS cnt
    FROM fact_orders
    GROUP BY order_id
    HAVING COUNT(*) > 1
) dupes
UNION ALL

-- [1b] Duplicate customer_id in dim_customers
SELECT 'FAIL: duplicate customer_id in dim_customers', COUNT(*)
FROM (
    SELECT customer_id, COUNT(*) AS cnt
    FROM dim_customers
    GROUP BY customer_id
    HAVING COUNT(*) > 1
) d
UNION ALL

-- [1c] Duplicate product_id in dim_products
SELECT 'FAIL: duplicate product_id in dim_products', COUNT(*)
FROM (
    SELECT product_id, COUNT(*) AS cnt
    FROM dim_products
    GROUP BY product_id
    HAVING COUNT(*) > 1
) d
UNION ALL

-- [1d] Duplicate date_key in dim_date
SELECT 'FAIL: duplicate date_key in dim_date', COUNT(*)
FROM (
    SELECT date_key, COUNT(*) AS cnt
    FROM dim_date
    GROUP BY date_key
    HAVING COUNT(*) > 1
) d;


-- ─────────────────────────────────────────────
-- 2. Foreign Key / Referential Integrity Checks
-- ─────────────────────────────────────────────

-- [2a] Orphaned customer_sk in fact_orders
SELECT 'FAIL: orphaned customer_sk in fact_orders' AS check_name,
       COUNT(*) AS violations
FROM fact_orders fo
LEFT JOIN dim_customers dc ON fo.customer_sk = dc.customer_sk
WHERE fo.customer_sk IS NOT NULL AND dc.customer_sk IS NULL
UNION ALL

-- [2b] Orphaned purchase_date_key in fact_orders
SELECT 'FAIL: orphaned purchase_date_key in fact_orders', COUNT(*)
FROM fact_orders fo
LEFT JOIN dim_date dd ON fo.purchase_date_key = dd.date_key
WHERE fo.purchase_date_key IS NOT NULL AND dd.date_key IS NULL;


-- ─────────────────────────────────────────────
-- 3. Revenue Validation
-- ─────────────────────────────────────────────

-- [3a] Compare total revenue: fact_orders vs stg_order_revenue
SELECT
    'Revenue reconciliation: fact vs staging' AS check_name,
    ABS(
        (SELECT COALESCE(SUM(order_revenue), 0) FROM fact_orders)
      - (SELECT COALESCE(SUM(order_revenue), 0) FROM stg_order_revenue)
    ) AS variance_brl;

-- [3b] Negative order_revenue in fact_orders
SELECT 'FAIL: negative order_revenue' AS check_name, COUNT(*) AS violations
FROM fact_orders
WHERE order_revenue < 0;

-- [3c] Orders with revenue but no payment recorded
SELECT 'WARN: orders with revenue but null payment_total' AS check_name,
       COUNT(*) AS violations
FROM fact_orders
WHERE order_revenue > 0 AND payment_total IS NULL;


-- ─────────────────────────────────────────────
-- 4. Order Count Validation
-- ─────────────────────────────────────────────

-- [4a] Order count: fact_orders vs stg_orders
SELECT
    'Order count: fact vs stg_orders' AS check_name,
    ABS(
        (SELECT COUNT(*) FROM fact_orders)
      - (SELECT COUNT(*) FROM stg_orders)
    ) AS count_diff;


-- ─────────────────────────────────────────────
-- 5. Null Checks on Critical Fields
-- ─────────────────────────────────────────────

SELECT 'FAIL: null order_id in fact_orders'       AS check_name, COUNT(*) FROM fact_orders WHERE order_id IS NULL
UNION ALL
SELECT 'FAIL: null customer_sk in fact_orders',    COUNT(*) FROM fact_orders WHERE customer_sk IS NULL
UNION ALL
SELECT 'FAIL: null order_status in fact_orders',   COUNT(*) FROM fact_orders WHERE order_status IS NULL;


-- ─────────────────────────────────────────────
-- 6. Delivery Logic Checks
-- ─────────────────────────────────────────────

-- [6a] Delivered before purchased
SELECT 'FAIL: delivered_date < purchase_date' AS check_name, COUNT(*) AS violations
FROM fact_orders
WHERE order_delivered_customer_date < order_purchase_timestamp;

-- [6b] Estimated delivery before purchased
SELECT 'FAIL: estimated_delivery < purchase_date', COUNT(*)
FROM fact_orders
WHERE order_estimated_delivery_date < order_purchase_timestamp;


-- ─────────────────────────────────────────────
-- 7. Summary Dashboard (run last)
-- ─────────────────────────────────────────────

SELECT
    (SELECT COUNT(*)         FROM fact_orders)          AS total_orders,
    (SELECT COUNT(DISTINCT customer_sk) FROM fact_orders) AS distinct_customers,
    (SELECT ROUND(SUM(order_revenue)::NUMERIC, 2)
     FROM fact_orders)                                  AS total_revenue_brl,
    (SELECT ROUND(AVG(order_revenue)::NUMERIC, 2)
     FROM fact_orders)                                  AS avg_order_value_brl,
    (SELECT ROUND(
        100.0 * SUM(is_late_delivery::INT)
                / NULLIF(COUNT(is_late_delivery), 0), 2)
     FROM fact_orders)                                  AS late_delivery_pct;
