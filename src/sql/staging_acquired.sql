-- Stage and normalize acquired PostgreSQL source rows.
--
-- Dialect: DuckDB (local Snowflake stand-in); Snowflake equivalents noted inline.
--
-- Handles the things the acquired source needs and the core one does not:
-- mixed date formats, multi-currency -> USD conversion, and duplicate rows.
-- Produces RAW.ACQUIRED_NORMALIZED with the same conformed schema as core.

CREATE OR REPLACE TABLE RAW.ACQUIRED_NORMALIZED AS
WITH joined AS (
    SELECT
        a.id,
        a.sale_date,
        a.customer_id,
        a.product_sku,
        a.total_price,
        a.currency,
        a.order_status,
        r.rate_to_usd,
        -- Duplicate detection: identical source transactions get rn > 1.
        ROW_NUMBER() OVER (
            PARTITION BY a.id
            ORDER BY a.id
        ) AS rn
    FROM RAW.STG_ACQUIRED_SALES a
    LEFT JOIN RAW.STG_EXCHANGE_RATES r
        ON a.currency = r.currency
)
SELECT
    'acquired'                               AS source_system,
    id                                       AS source_transaction_id,
    'acquired:' || id                        AS warehouse_transaction_id,
    -- Mixed date formats: try day-first DD/MM/YYYY, then year-first YYYY/MM/DD.
    -- Snowflake: COALESCE(TRY_TO_TIMESTAMP(sale_date,'DD/MM/YYYY HH24:MI:SS'),
    --                     TRY_TO_TIMESTAMP(sale_date,'YYYY/MM/DD HH24:MI:SS'))
    COALESCE(
        TRY_STRPTIME(sale_date, '%d/%m/%Y %H:%M:%S'),
        TRY_STRPTIME(sale_date, '%Y/%m/%d %H:%M:%S')
    )                                        AS checkout_timestamp,
    TRY_CAST(customer_id AS BIGINT)          AS customer_id,
    CAST(NULL AS VARCHAR)                    AS customer_country,  -- acquired has no country
    NULLIF(regexp_replace(product_sku, '^[A-Za-z]+-', ''), '') AS sku,
    -- Currency normalization to USD (NULL rate -> NULL, row is rejected below).
    ROUND(CAST(total_price AS DOUBLE) * CAST(rate_to_usd AS DOUBLE), 2) AS gross_amount_usd,
    CAST(0.00 AS DOUBLE)                     AS tax_amount_usd,    -- acquired has no tax
    FALSE                                    AS is_refunded,       -- acquired has no refund flag
    -- Data-quality rules (first match wins): duplicate, then unknown currency.
    CASE
        WHEN rn > 1               THEN 'duplicate_source_transaction'
        WHEN rate_to_usd IS NULL  THEN 'unknown_currency'
        ELSE ''
    END                                      AS reject_reason
FROM joined;
