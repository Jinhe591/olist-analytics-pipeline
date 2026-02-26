USE olist_warehouse;
LOAD DATA LOCAL INFILE 'data/processed/olist_customers_dataset_clean.csv'
INTO TABLE stg_customers
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
customer_id,
customer_unique_id,
customer_zip_code_prefix,
customer_city,
customer_state
);