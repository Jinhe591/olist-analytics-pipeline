# Power BI DAX Measures Reference
## Olist E-Commerce Dashboard

This file documents all DAX measures used in `olist_dashboard.pbix`.
Copy these into the Power BI Desktop DAX editor when building the semantic model.

---

## Revenue Measures

```dax
-- ── Core Revenue ──────────────────────────────────────────────

Total Revenue =
    CALCULATE(
        SUM(fact_orders[order_revenue]),
        fact_orders[order_status] <> "canceled",
        fact_orders[order_status] <> "unavailable"
    )

Total Freight =
    CALCULATE(
        SUM(fact_orders[order_freight]),
        fact_orders[order_status] <> "canceled",
        fact_orders[order_status] <> "unavailable"
    )

Total Order Value =
    [Total Revenue] + [Total Freight]

Total Orders =
    CALCULATE(
        COUNTROWS(fact_orders),
        fact_orders[order_status] <> "canceled",
        fact_orders[order_status] <> "unavailable"
    )

AOV =
    DIVIDE([Total Revenue], [Total Orders])

Revenue per Customer =
    DIVIDE(
        [Total Revenue],
        DISTINCTCOUNT(fact_orders[customer_sk])
    )

-- ── Growth Metrics ────────────────────────────────────────────

Revenue MoM Growth % =
VAR CurrentRevenue = [Total Revenue]
VAR PrevRevenue =
    CALCULATE(
        [Total Revenue],
        DATEADD(dim_date[full_date], -1, MONTH)
    )
RETURN
    DIVIDE(CurrentRevenue - PrevRevenue, PrevRevenue)

Revenue YoY Growth % =
VAR CurrentRevenue = [Total Revenue]
VAR PrevRevenue =
    CALCULATE(
        [Total Revenue],
        DATEADD(dim_date[full_date], -1, YEAR)
    )
RETURN
    DIVIDE(CurrentRevenue - PrevRevenue, PrevRevenue)

Revenue YTD =
    TOTALYTD([Total Revenue], dim_date[full_date])

Revenue Running Total =
    CALCULATE(
        [Total Revenue],
        DATESYTD(dim_date[full_date])
    )

-- ── Cumulative / Period Analysis ──────────────────────────────

Revenue Last 3 Months =
    CALCULATE(
        [Total Revenue],
        DATESINPERIOD(dim_date[full_date], LASTDATE(dim_date[full_date]), -3, MONTH)
    )

Revenue Last 12 Months =
    CALCULATE(
        [Total Revenue],
        DATESINPERIOD(dim_date[full_date], LASTDATE(dim_date[full_date]), -12, MONTH)
    )
```

---

## Delivery Performance Measures

```dax
-- ── Delivery KPIs ─────────────────────────────────────────────

On-Time Deliveries =
    CALCULATE(
        COUNTROWS(fact_orders),
        fact_orders[is_late_delivery] = FALSE(),
        fact_orders[order_status] = "delivered"
    )

Late Deliveries =
    CALCULATE(
        COUNTROWS(fact_orders),
        fact_orders[is_late_delivery] = TRUE(),
        fact_orders[order_status] = "delivered"
    )

Total Delivered Orders =
    CALCULATE(
        COUNTROWS(fact_orders),
        fact_orders[order_status] = "delivered",
        NOT ISBLANK(fact_orders[is_late_delivery])
    )

On-Time Delivery % =
    DIVIDE([On-Time Deliveries], [Total Delivered Orders])

Late Delivery % =
    DIVIDE([Late Deliveries], [Total Delivered Orders])

Avg Delivery Days =
    CALCULATE(
        AVERAGE(fact_orders[delivery_duration_days]),
        fact_orders[order_status] = "delivered",
        NOT ISBLANK(fact_orders[delivery_duration_days])
    )

Avg Late Delivery Days =
    CALCULATE(
        AVERAGE(fact_orders[delivery_duration_days]),
        fact_orders[is_late_delivery] = TRUE()
    )

Avg On-Time Delivery Days =
    CALCULATE(
        AVERAGE(fact_orders[delivery_duration_days]),
        fact_orders[is_late_delivery] = FALSE()
    )
```

---

## Customer Measures

```dax
-- ── Customer KPIs ─────────────────────────────────────────────

Unique Customers =
    DISTINCTCOUNT(fact_orders[customer_sk])

New Customers This Period =
    CALCULATE(
        DISTINCTCOUNT(fact_orders[customer_sk]),
        FILTER(
            fact_orders,
            CALCULATE(
                COUNTROWS(fact_orders),
                DATESBETWEEN(
                    dim_date[full_date],
                    DATE(2000,1,1),
                    MAX(dim_date[full_date]) - 1
                )
            ) = 0
        )
    )

Revenue per Unique Customer =
    DIVIDE([Total Revenue], [Unique Customers])

Avg Orders per Customer =
    DIVIDE([Total Orders], [Unique Customers])
```

---

## Product / Category Measures

```dax
-- ── Product KPIs ──────────────────────────────────────────────

Category Revenue =
    SUMX(
        fact_order_items,
        fact_order_items[price]
    )

Category Revenue % of Total =
    DIVIDE(
        [Category Revenue],
        CALCULATE([Category Revenue], ALL(dim_products[product_category_name_english]))
    )

Avg Item Price =
    AVERAGE(fact_order_items[price])

Total Items Sold =
    COUNTROWS(fact_order_items)

Unique Products Sold =
    DISTINCTCOUNT(fact_order_items[product_sk])
```

---

## Formatting Measures (for Card Visuals)

```dax
-- Formatted currency
Total Revenue (BRL) =
    FORMAT([Total Revenue], "R$ #,##0.00")

-- Formatted percentage
On-Time % Label =
    FORMAT([On-Time Delivery %], "0.0%")

-- Conditional color for growth
Revenue Growth Colour =
    IF([Revenue MoM Growth %] >= 0, "#27AE60", "#E74C3C")
```

---

## Semantic Model Relationships

| From Table | Column | To Table | Column | Cardinality |
|------------|--------|----------|--------|-------------|
| fact_orders | customer_sk | dim_customers | customer_sk | Many:1 |
| fact_orders | purchase_date_key | dim_date | date_key | Many:1 |
| fact_order_items | order_sk | fact_orders | order_sk | Many:1 |
| fact_order_items | product_sk | dim_products | product_sk | Many:1 |
| fact_order_items | seller_sk | dim_sellers | seller_sk | Many:1 |
| fact_order_items | purchase_date_key | dim_date | date_key | Many:1 |

> All relationships use single-directional cross-filter from dimension → fact.
> Enable bidirectional filtering only where explicitly required for a visual.
