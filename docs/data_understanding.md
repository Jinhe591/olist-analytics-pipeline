Customers Dataset

    99,441 rows and 5 columns

    Primary key is customer_id

    No missing values found

    No duplicate rows found

    Each customer can have multiple orders (same customer_unique_id appears multiple times)

Orders Dataset

    99,441 rows and 8 columns

    Primary key is order_id

    Missing values found in date columns:

        order_delivered_customer_date: 2,965 missing (orders not delivered yet)

        order_delivered_carrier_date: 1,783 missing

        order_approved_at: 160 missing

    All date columns are stored as strings, need to convert to datetime

    No duplicate rows found

Order Items Dataset

    112,650 rows and 7 columns

    Composite key is order_id + order_item_id

    No missing values found

    No duplicate rows found

    Connects orders to products and sellers

Products Dataset

    32,951 rows and 9 columns

    Primary key is product_id

    Missing values found:

        610 products missing category name, name length, description length, photo count

        2 products missing weight and dimensions

    No duplicate rows found

Payments Dataset

    103,886 rows and 5 columns

    No missing values

    No duplicates

    Some orders have multiple payment methods

Reviews Dataset

    99,224 rows and 7 columns

    Missing values:

        review_comment_title: 87,656 missing (88%)

        review_comment_message: 58,247 missing (58%)

    No duplicate rows found

Sellers Dataset

    3,095 rows and 4 columns

    No missing values

    No duplicates

Geolocation Dataset

    1,000,163 rows and 5 columns

    No missing values

    261,831 duplicate rows found (26% of data)

    Same zip code appears multiple times with different coordinates

Category Translation Dataset

    71 rows and 2 columns

    Maps Portuguese category names to English

    No missing values or duplicates

Relationships Between Tables

    orders connects to customers via customer_id

    orders connects to order_items via order_id

    order_items connects to products via product_id

    order_items connects to sellers via seller_id

    orders connects to payments via order_id

    orders connects to reviews via order_id

    products connects to category_translation via product_category_name

Main Data Issues Found

    Geolocation dataset has 261,831 duplicate rows (26%)

    610 products missing category information

    2,965 orders missing delivery dates

    Most reviews are missing text comments (88% no title, 58% no message)

    All date fields are stored as strings, need conversion

    Products with missing category also missing other product info