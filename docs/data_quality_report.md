Null Checks

orders_dataset.csv:

    order_delivered_customer_date: 2,965 nulls

    order_delivered_carrier_date: 1,783 nulls

    order_approved_at: 160 nulls

products_dataset.csv:

    product_category_name: 610 nulls

    product_name_lenght: 610 nulls

    product_description_lenght: 610 nulls

    product_photos_qty: 610 nulls

    product_weight_g: 2 nulls

    product_length_cm: 2 nulls

    product_height_cm: 2 nulls

    product_width_cm: 2 nulls

order_reviews_dataset.csv:

    review_comment_title: 87,656 nulls

    review_comment_message: 58,247 nulls

All other datasets have no null values.
Duplicate Checks

geolocation_dataset.csv:

    Total rows: 1,000,163

    Duplicate rows: 261,831

    Duplicate rate: 26%

All other datasets have no duplicate rows.
Revenue Validation

I checked if the total revenue matches between order_items and payments:

order_items total (price + freight_value): R$ 13,516,415.82
payments total (payment_value): R$ 13,516,415.82

The totals match exactly.

When checking order by order:

    98,892 orders match perfectly (99.45%)

    549 orders have small differences (less than R$0.01)

    This is probably due to floating point math or multiple payments per order

Delivery Validation

Delivery Status:

    Delivered: 96,476 orders (97%)

    Not delivered: 2,965 orders (3%)

For delivered orders:

    Average delivery time: 12.5 days

    Fastest delivery: 0 days

    Slowest delivery: 209 days

On-time Performance:

    Delivered on or before estimated date: 92,043 orders (95.4%)

    Delivered late: 4,433 orders (4.6%)

    Average days late: 8.3 days

Date Order Check:
I checked if dates make sense (purchase before approval, approval before delivery, etc.) and found no issues. All dates are in the correct order.
Summary of Findings

Good:

    Most tables are clean with no nulls

    Revenue numbers match across tables

    Date logic is consistent

    Primary keys work as expected

Bad:

    Geolocation has 261k duplicates (need to fix)

    610 products missing categories (need to handle)

    2,965 orders missing delivery dates

    88% of reviews missing titles, 58% missing messages

Need to Fix:

    Remove duplicates from geolocation

    Handle missing product categories (fill with "unknown" or something)

    Convert all date strings to datetime

    Decide what to do with missing review text