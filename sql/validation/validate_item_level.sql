-- =============================================================
-- validation/validate_item_level.sql
--
-- Additional validation queries for fact_order_items and
-- cross-grain consistency between fact_orders and fact_order_items.
-- =============================================================


-- ─────────────────────────────────────────────
-- 1. Cross-grain revenue consistency
-- Revenue summed from item level should match order-level revenue
-- (within a small tolerance for rounding)
-- ─────────────────────────────────────────────

SELECT
    'Item-level revenue vs order-level revenue' AS check_name,
    ROUND(
        ABS(
            (SELECT SUM(price) FROM fact_order_items)
          - (SELECT SUM(order_revenue) FROM fact_orders)
        )::NUMERIC, 2
    ) AS variance_brl;


-- ─────────────────────────────────────────────
-- 2. Every item maps to a valid order
-- ─────────────────────────────────────────────

SELECT 'FAIL: order_items with no matching order_sk' AS check_name,
       COUNT(*) AS violations
FROM fact_order_items
WHERE order_sk IS NULL;


-- ─────────────────────────────────────────────
-- 3. Product coverage: items with no product_sk
-- ─────────────────────────────────────────────

SELECT 'WARN: order_items with no product_sk (product not in dim)' AS check_name,
       COUNT(*) AS violations
FROM fact_order_items
WHERE product_sk IS NULL;


-- ─────────────────────────────────────────────
-- 4. Negative prices
-- ─────────────────────────────────────────────

SELECT 'FAIL: negative price in fact_order_items' AS check_name,
       COUNT(*) AS violations
FROM fact_order_items
WHERE price < 0;

SELECT 'FAIL: negative freight_value in fact_order_items' AS check_name,
       COUNT(*) AS violations
FROM fact_order_items
WHERE freight_value < 0;


-- ─────────────────────────────────────────────
-- 5. Category revenue sanity — top 10 categories
-- Use for manual spot-check in dashboard
-- ─────────────────────────────────────────────

SELECT
    dp.product_category_name_english        AS category,
    COUNT(DISTINCT foi.order_id)            AS total_orders,
    COUNT(foi.item_sk)                      AS total_items,
    ROUND(SUM(foi.price)::NUMERIC, 2)       AS total_revenue,
    ROUND(AVG(foi.price)::NUMERIC, 2)       AS avg_item_price
FROM fact_order_items foi
JOIN dim_products dp ON foi.product_sk = dp.product_sk
GROUP BY dp.product_category_name_english
ORDER BY total_revenue DESC
LIMIT 10;


-- ─────────────────────────────────────────────
-- 6. Seller coverage
-- ─────────────────────────────────────────────

SELECT
    'Sellers in items not in dim_sellers' AS check_name,
    COUNT(*) AS violations
FROM fact_order_items
WHERE seller_sk IS NULL;


-- ─────────────────────────────────────────────
-- 7. Full validation summary (pass/fail report)
-- All rows should show 0 violations
-- ─────────────────────────────────────────────

WITH checks AS (
    SELECT 'Duplicate order_id in fact_orders'           AS check_name,
           COUNT(*) AS violations
    FROM (SELECT order_id FROM fact_orders GROUP BY order_id HAVING COUNT(*) > 1) d

    UNION ALL SELECT 'Duplicate (order_id, item_id) in fact_order_items',
           COUNT(*)
    FROM (SELECT order_id, order_item_id FROM fact_order_items
          GROUP BY order_id, order_item_id HAVING COUNT(*) > 1) d

    UNION ALL SELECT 'Orphaned customer_sk in fact_orders',
           COUNT(*) FROM fact_orders fo
    LEFT JOIN dim_customers dc ON fo.customer_sk = dc.customer_sk
    WHERE fo.customer_sk IS NOT NULL AND dc.customer_sk IS NULL

    UNION ALL SELECT 'Orphaned purchase_date_key in fact_orders',
           COUNT(*) FROM fact_orders fo
    LEFT JOIN dim_date dd ON fo.purchase_date_key = dd.date_key
    WHERE fo.purchase_date_key IS NOT NULL AND dd.date_key IS NULL

    UNION ALL SELECT 'Negative order_revenue in fact_orders',
           COUNT(*) FROM fact_orders WHERE order_revenue < 0

    UNION ALL SELECT 'Delivered before purchased in fact_orders',
           COUNT(*) FROM fact_orders
    WHERE order_delivered_customer_date < order_purchase_timestamp

    UNION ALL SELECT 'Negative price in fact_order_items',
           COUNT(*) FROM fact_order_items WHERE price < 0

    UNION ALL SELECT 'Items with no order_sk',
           COUNT(*) FROM fact_order_items WHERE order_sk IS NULL
)
SELECT
    check_name,
    violations,
    CASE WHEN violations = 0 THEN 'PASS ✓' ELSE 'FAIL ✗' END AS status
FROM checks
ORDER BY violations DESC;
