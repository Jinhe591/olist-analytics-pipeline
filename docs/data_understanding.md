# Data Understanding Report
## Olist E-Commerce Dataset

**Author:** Analytics Engineering Team  
**Dataset:** [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)  
**Last Updated:** 2024

---

## 1. Dataset Overview

The Olist dataset contains anonymised commercial data from the Olist Store, a Brazilian e-commerce marketplace connector that allows small merchants to sell through major Brazilian e-commerce platforms. The dataset covers orders placed between **October 2016 and September 2018**.

---

## 2. Table-by-Table Analysis

### 2.1 Customers (`olist_customers_dataset.csv`)

| Attribute | Value |
|-----------|-------|
| **Business Purpose** | Maps each order to a unique customer and their location |
| **Grain** | One row per `customer_id` (a customer may appear multiple times with different `customer_id` values if they placed multiple orders, but they share the same `customer_unique_id`) |
| **Approx. Rows** | ~99,441 |
| **Columns** | 5 |

**Schema**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `customer_id` | VARCHAR | No | **Primary Key** — unique per order |
| `customer_unique_id` | VARCHAR | No | **Candidate Key** — deduplicated customer identifier |
| `customer_zip_code_prefix` | VARCHAR | No | 5-digit ZIP prefix |
| `customer_city` | VARCHAR | No | Customer's city |
| `customer_state` | CHAR(2) | No | 2-letter Brazilian state code |

**Key Observations**
- `customer_id` is intentionally non-unique across the customer table: each order creates a new `customer_id` for privacy reasons.
- `customer_unique_id` should be used for customer-level repeat-purchase analysis.
- City names contain inconsistent casing and occasional typos.
- State codes are standard 2-letter Brazilian codes; occasional anomalies exist.

**Data Quality Issues Found**
- ~0.1% of city names contain leading/trailing whitespace
- Mixed-case city names (e.g. "são paulo" vs "São Paulo")
- No null values on primary key columns

---

### 2.2 Orders (`olist_orders_dataset.csv`)

| Attribute | Value |
|-----------|-------|
| **Business Purpose** | Central order lifecycle table — tracks status and timestamps |
| **Grain** | One row per `order_id` |
| **Approx. Rows** | ~99,441 |
| **Columns** | 8 (plus derived) |

**Schema**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `order_id` | VARCHAR | No | **Primary Key** |
| `customer_id` | VARCHAR | No | **FK → customers.customer_id** |
| `order_status` | VARCHAR | No | Current order status |
| `order_purchase_timestamp` | TIMESTAMP | No | When the order was placed |
| `order_approved_at` | TIMESTAMP | Yes | Payment approval time |
| `order_delivered_carrier_date` | TIMESTAMP | Yes | Handoff to carrier |
| `order_delivered_customer_date` | TIMESTAMP | Yes | Actual delivery date |
| `order_estimated_delivery_date` | TIMESTAMP | No | Seller's estimated delivery |

**Order Status Distribution (Approximate)**

| Status | % of Orders |
|--------|------------|
| delivered | ~96.5% |
| shipped | ~1.1% |
| canceled | ~0.6% |
| unavailable | ~0.9% |
| Others | ~0.9% |

**Data Quality Issues Found**
- ~1,600 orders missing `order_approved_at` (typically canceled orders)
- ~2,980 orders missing `order_delivered_customer_date` (not yet delivered)
- Small number of orders with `estimated_delivery_date` before `purchase_timestamp`
- Timestamp columns stored as VARCHAR in source — require explicit parsing

---

### 2.3 Order Items (`olist_order_items_dataset.csv`)

| Attribute | Value |
|-----------|-------|
| **Business Purpose** | Line items within each order — products, sellers, pricing |
| **Grain** | One row per order-item (composite key: `order_id` + `order_item_id`) |
| **Approx. Rows** | ~112,650 |
| **Columns** | 7 |

**Schema**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `order_id` | VARCHAR | No | **FK → orders.order_id** |
| `order_item_id` | INTEGER | No | Item sequence within the order (1, 2, 3…) |
| `product_id` | VARCHAR | No | **FK → products.product_id** |
| `seller_id` | VARCHAR | No | Seller who fulfilled this item |
| `shipping_limit_date` | TIMESTAMP | No | Last date seller can ship |
| `price` | NUMERIC | No | Item price in BRL |
| `freight_value` | NUMERIC | No | Freight charged for this item |

**Key Observations**
- An order can contain items from multiple sellers
- ~1% of orders contain more than one item
- Composite PK: (`order_id`, `order_item_id`)

---

### 2.4 Products (`olist_products_dataset.csv`)

| Attribute | Value |
|-----------|-------|
| **Business Purpose** | Product catalogue with physical attributes |
| **Grain** | One row per `product_id` |
| **Approx. Rows** | ~32,951 |
| **Columns** | 9 |

**Schema**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `product_id` | VARCHAR | No | **Primary Key** |
| `product_category_name` | VARCHAR | Yes | Portuguese category name |
| `product_name_lenght` | INTEGER | Yes | Character length of name |
| `product_description_lenght` | INTEGER | Yes | Character length of description |
| `product_photos_qty` | SMALLINT | Yes | Number of product photos |
| `product_weight_g` | NUMERIC | Yes | Weight in grams |
| `product_length_cm` | NUMERIC | Yes | Length in cm |
| `product_height_cm` | NUMERIC | Yes | Height in cm |
| `product_width_cm` | NUMERIC | Yes | Width in cm |

**Data Quality Issues Found**
- ~610 products have null `product_category_name` → mapped to "uncategorized"
- Physical dimensions (weight, size) are null for ~2% of products
- Category names are in Portuguese; translated via `product_category_name_translation.csv`

---

## 3. Relationship Mapping

```
customers (1) ──── (N) orders
                         │
orders (1) ──────── (N) order_items
                         │
products (1) ───── (N) order_items
                         │
sellers (1) ──────── (N) order_items

orders (1) ──────── (N) order_payments
orders (1) ──────── (N) order_reviews
```

### Cardinality Summary

| Relationship | Type | Notes |
|---|---|---|
| customers → orders | 1:N | Each `customer_id` appears once in customers; orders has FK |
| orders → order_items | 1:N | ~1 item per order average |
| products → order_items | 1:N | Product can appear in many orders |
| sellers → order_items | 1:N | Seller fulfils multiple items |
| orders → order_payments | 1:N | One order can have split payments |
| orders → order_reviews | 1:1 | One review per delivered order (approximate) |

---

## 4. ERD Recommendations

For the star schema, implement:

- **Fact table:** `fact_orders` (order grain)
- **Dimensions:** `dim_customers`, `dim_products`, `dim_date`
- **Degenerate dimensions:** `order_status`, `order_id` stored in fact table
- **Bridge/helper tables:** Not required at order grain; join to `stg_order_items` for product-level analysis

---

## 5. Analytical Scope

The dataset supports the following analytical use cases:

1. **Revenue Analytics** — total GMV, AOV, revenue by time/geography/category
2. **Customer Analytics** — new vs repeat customers, geographic distribution
3. **Product Analytics** — category performance, top products, price distribution
4. **Delivery Performance** — on-time rate, average duration, delay hotspots
5. **Seller Performance** — seller revenue contribution, fulfillment speed
6. **Payment Analytics** — payment method mix, installment behaviour
