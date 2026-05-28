-- =============================================================
-- dimensions/dim_sellers.sql
-- Seller dimension populated from stg_sellers.
-- NOTE: stg_sellers is loaded by the Python pipeline BEFORE
--       this script runs. Do NOT drop or recreate stg_sellers here.
-- =============================================================

DROP TABLE IF EXISTS dim_sellers CASCADE;

CREATE TABLE dim_sellers (
    seller_sk               SERIAL       NOT NULL,
    seller_id               VARCHAR(50)  NOT NULL,
    seller_zip_code_prefix  VARCHAR(10),
    seller_city             VARCHAR(100),
    seller_state            CHAR(2),
    CONSTRAINT pk_dim_sellers    PRIMARY KEY (seller_sk),
    CONSTRAINT uq_dim_sellers_bk UNIQUE (seller_id)
);

COMMENT ON TABLE dim_sellers IS
    'Seller dimension. Grain: one row per seller_id.';

INSERT INTO dim_sellers (
    seller_id, seller_zip_code_prefix, seller_city, seller_state
)
SELECT
    seller_id,
    seller_zip_code_prefix,
    INITCAP(TRIM(seller_city)),
    UPPER(TRIM(seller_state))
FROM stg_sellers;

CREATE INDEX idx_dim_sellers_state ON dim_sellers (seller_state);