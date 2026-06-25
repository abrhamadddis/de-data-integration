-- Merge staged rows into final Snowflake fact and reject tables.
--
-- Dialect: DuckDB (local Snowflake stand-in). The delete-then-insert below is
-- the portable, idempotent form of an upsert; on Snowflake this is normally a
-- single MERGE INTO ... USING ... WHEN MATCHED THEN UPDATE WHEN NOT MATCHED
-- THEN INSERT, keyed on warehouse_transaction_id.

CREATE SCHEMA IF NOT EXISTS ANALYTICS;

CREATE TABLE IF NOT EXISTS ANALYTICS.SALES_FACT (
    source_system            VARCHAR,
    source_transaction_id    VARCHAR,
    warehouse_transaction_id VARCHAR,
    checkout_timestamp       TIMESTAMP,
    customer_id              BIGINT,
    customer_country         VARCHAR,
    sku                      VARCHAR,
    gross_amount_usd         DOUBLE,
    tax_amount_usd           DOUBLE,
    is_refunded              BOOLEAN
);

CREATE TABLE IF NOT EXISTS ANALYTICS.SALES_REJECTS (
    source_system         VARCHAR,
    source_transaction_id VARCHAR,
    reject_reason         VARCHAR
);

-- Combine both conformed sources into one set.
CREATE OR REPLACE TABLE RAW.ALL_NORMALIZED AS
SELECT * FROM RAW.CORE_NORMALIZED
UNION ALL
SELECT * FROM RAW.ACQUIRED_NORMALIZED;

-- ---- Load valid rows into the fact table (idempotent upsert) ----
DELETE FROM ANALYTICS.SALES_FACT
WHERE warehouse_transaction_id IN (
    SELECT warehouse_transaction_id FROM RAW.ALL_NORMALIZED WHERE reject_reason = ''
);

INSERT INTO ANALYTICS.SALES_FACT
SELECT
    source_system,
    source_transaction_id,
    warehouse_transaction_id,
    checkout_timestamp,
    customer_id,
    customer_country,
    sku,
    gross_amount_usd,
    tax_amount_usd,
    is_refunded
FROM RAW.ALL_NORMALIZED
WHERE reject_reason = '';

-- ---- Load rejected rows into the rejects table (idempotent upsert) ----
DELETE FROM ANALYTICS.SALES_REJECTS
WHERE (source_system, source_transaction_id) IN (
    SELECT source_system, source_transaction_id
    FROM RAW.ALL_NORMALIZED
    WHERE reject_reason <> ''
);

INSERT INTO ANALYTICS.SALES_REJECTS
SELECT source_system, source_transaction_id, reject_reason
FROM RAW.ALL_NORMALIZED
WHERE reject_reason <> '';
