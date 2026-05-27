-- =============================================================
-- dimensions/dim_date.sql
-- Generates a fully populated date dimension spanning
-- 2016-01-01 to 2019-12-31 (covers all Olist order data).
-- =============================================================

DROP TABLE IF EXISTS dim_date CASCADE;

CREATE TABLE dim_date (
    date_key            INTEGER       NOT NULL,  -- YYYYMMDD surrogate key
    full_date           DATE          NOT NULL,
    year                SMALLINT      NOT NULL,
    quarter             SMALLINT      NOT NULL,
    month               SMALLINT      NOT NULL,
    month_name          VARCHAR(10)   NOT NULL,
    month_name_short    CHAR(3)       NOT NULL,
    week_of_year        SMALLINT      NOT NULL,
    day_of_year         SMALLINT      NOT NULL,
    day_of_month        SMALLINT      NOT NULL,
    day_of_week         SMALLINT      NOT NULL,  -- 1=Sunday … 7=Saturday
    day_name            VARCHAR(10)   NOT NULL,
    day_name_short      CHAR(3)       NOT NULL,
    is_weekend          BOOLEAN       NOT NULL,
    quarter_label       VARCHAR(7)    NOT NULL,  -- e.g. 'Q1-2018'
    year_month          VARCHAR(7)    NOT NULL,  -- e.g. '2018-03'
    CONSTRAINT pk_dim_date PRIMARY KEY (date_key)
);

COMMENT ON TABLE dim_date IS
    'Date dimension: one row per calendar day from 2016-01-01 to 2019-12-31.';

-- ── Populate via generate_series ────────────
INSERT INTO dim_date (
    date_key, full_date, year, quarter, month, month_name,
    month_name_short, week_of_year, day_of_year, day_of_month,
    day_of_week, day_name, day_name_short, is_weekend,
    quarter_label, year_month
)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER                         AS date_key,
    d                                                        AS full_date,
    EXTRACT(YEAR   FROM d)::SMALLINT                        AS year,
    EXTRACT(QUARTER FROM d)::SMALLINT                       AS quarter,
    EXTRACT(MONTH  FROM d)::SMALLINT                        AS month,
    TO_CHAR(d, 'Month')                                     AS month_name,
    TO_CHAR(d, 'Mon')                                       AS month_name_short,
    EXTRACT(WEEK   FROM d)::SMALLINT                        AS week_of_year,
    EXTRACT(DOY    FROM d)::SMALLINT                        AS day_of_year,
    EXTRACT(DAY    FROM d)::SMALLINT                        AS day_of_month,
    EXTRACT(DOW    FROM d)::SMALLINT + 1                    AS day_of_week,
    TO_CHAR(d, 'Day')                                       AS day_name,
    TO_CHAR(d, 'Dy')                                        AS day_name_short,
    EXTRACT(DOW FROM d) IN (0, 6)                           AS is_weekend,
    'Q' || EXTRACT(QUARTER FROM d)::TEXT
        || '-' || EXTRACT(YEAR FROM d)::TEXT                AS quarter_label,
    TO_CHAR(d, 'YYYY-MM')                                   AS year_month
FROM
    GENERATE_SERIES('2016-01-01'::DATE, '2019-12-31'::DATE, '1 day'::INTERVAL) AS d;

-- ── Index for common join patterns ──────────
CREATE INDEX idx_dim_date_full_date    ON dim_date (full_date);
CREATE INDEX idx_dim_date_year_month   ON dim_date (year, month);
CREATE INDEX idx_dim_date_year         ON dim_date (year);
