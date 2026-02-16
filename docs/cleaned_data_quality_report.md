1. Null Checks

    Customers: No missing values

    Orders:

        order_approved_at: 160 missing

        order_delivered_carrier_date: 1,783 missing

        order_delivered_customer_date: 2,965 missing

    Products: No missing values (all filled during cleaning)

    Items: No missing values

    Payments: No missing values

    Reviews: No missing values (titles/messages filled with empty string)

    Revenue: 1 missing record (from left join)

    Sellers: No missing values

2. Duplicate Checks

All datasets have 0 duplicates after cleaning.
3. Revenue Validation

    Matching orders: 98,287

    Total orders compared: 98,665

    Match rate: 99.62%

4. Delivery Validation

    Total orders: 99,441

    Delivered: 96,476 (97%)

    Not delivered: 2,965 (3%)

    Late deliveries: 6,535

Summary

All datasets cleaned and saved in 
data/processed/
Ready for analysis.