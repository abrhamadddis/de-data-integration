-- Stage and normalize core SQL Server source rows.
--
-- Dialect: DuckDB (the local Snowflake stand-in). Snowflake equivalents are
-- noted inline so this logic can be ported to a live warehouse.
--
-- Produces RAW.CORE_NORMALIZED with the conformed warehouse schema plus a
-- reject_reason column ('' means the row is valid).

CREATE OR REPLACE TABLE RAW.CORE_NORMALIZED AS
SELECT
    'core'                                   AS source_system,
    tx_id                                    AS source_transaction_id,
    'core:' || tx_id                         AS warehouse_transaction_id,
    -- Core timestamps are already ISO (YYYY-MM-DD HH:MM:SS).
    CAST(checkout_timestamp AS TIMESTAMP)    AS checkout_timestamp,
    -- Parse the customer JSON blob. Guarded by json_valid so a bad blob does
    -- not error (it is rejected below instead).
    -- Snowflake: TRY_PARSE_JSON(customer_blob):id::number
    CASE WHEN json_valid(customer_blob)
         THEN TRY_CAST(json_extract_string(customer_blob, '$.id') AS BIGINT)
    END                                      AS customer_id,
    -- Snowflake: TRY_PARSE_JSON(customer_blob):country::string
    CASE WHEN json_valid(customer_blob)
         THEN json_extract_string(customer_blob, '$.country')
    END                                      AS customer_country,
    -- SKU cleanup: strip a leading alpha prefix + dash (PROD-, SKU-).
    -- Snowflake: REGEXP_REPLACE(sku_code, '^[A-Za-z]+-', '')
    NULLIF(regexp_replace(sku_code, '^[A-Za-z]+-', ''), '') AS sku,
    CAST(gross_amt_usd AS DOUBLE)            AS gross_amount_usd,  -- core is already USD
    CAST(tax_amt AS DOUBLE)                  AS tax_amount_usd,
    (is_refunded = '1')                      AS is_refunded,       -- 0/1 -> boolean
    -- Data-quality rules (first match wins): invalid JSON, then missing SKU.
    CASE
        WHEN NOT json_valid(customer_blob)        THEN 'invalid_customer_blob'
        WHEN TRIM(COALESCE(sku_code, '')) = ''    THEN 'missing_sku'
        ELSE ''
    END                                      AS reject_reason
FROM RAW.STG_CORE_SALES;
