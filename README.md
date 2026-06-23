# Enterprise Data Integration Take-Home

Build a Python + SQL pipeline that combines sales data from a core SQL Server
source and an acquired PostgreSQL source into a Snowflake sales fact table.


## Inputs

Use the CSV fixtures in `data/`:

- `sqlserver_mock.csv`: core SQL Server sales.
- `postgres_mock.csv`: acquired PostgreSQL sales.
- `exchange_rates.csv`: currency conversion rates.
- `expected_sales_fact.csv`: expected final fact output.
- `expected_rejects.csv`: expected rejected records.

## Requirements

- Implement an OOP Python pipeline with `main.py` as the entry point.
- Use an abstract extractor contract, concrete SQL Server/PostgreSQL extractors,
  a Snowflake staging loader, and a reusable SQL script runner.
- Process sources polymorphically from the orchestrator.
- Run locally from the provided CSVs; live SQL Server/PostgreSQL instances are
  not required.
- Load staged source data and final transformed outputs into Snowflake.
- Put Snowflake-native transformations in `src/sql/`.
- Do not hard-code secrets or connection strings.
- Read Snowflake connection settings from environment variables or a local
  ignored config file.

## Transformations To Handle

- Source-prefixed warehouse keys, e.g. `core:9001` and `acquired:9001`.
- Currency normalization to USD.
- SQL Server `customer_blob` JSON parsing.
- Mixed date format normalization.
- SKU cleanup from prefixes such as `PROD-` and `SKU-`.
- Duplicate source transaction detection.
- Reject handling for invalid JSON, missing SKU, unknown currency, and
  duplicates.

## Expected Output

After processing SQL Server and PostgreSQL data, the final fact table should
be written to Snowflake and match `data/expected_sales_fact.csv`.

Rejected rows should be written to Snowflake and match
`data/expected_rejects.csv`.

Suggested Snowflake objects:

```text
DE_INTEGRATION.RAW.STG_CORE_SALES
DE_INTEGRATION.RAW.STG_ACQUIRED_SALES
DE_INTEGRATION.RAW.STG_EXCHANGE_RATES
DE_INTEGRATION.ANALYTICS.SALES_FACT
DE_INTEGRATION.ANALYTICS.SALES_REJECTS
```

Required fact columns:

```text
source_system
source_transaction_id
warehouse_transaction_id
checkout_timestamp
customer_id
customer_country
sku
gross_amount_usd
tax_amount_usd
is_refunded
```

## Project Layout : Feel free to change

```text
config/settings.py
data/*.csv
main.py
src/extractors/base_extractor.py
src/extractors/postgres.py
src/extractors/sqlserver.py
src/loaders/snowflake.py
src/sql/staging_core.sql
src/sql/staging_acquired.sql
src/sql/warehouse_merge.sql
src/transformers/sql_runner.py
tests/
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run:

```bash
python main.py
```

Example Snowflake environment variables:

```bash
export SNOWFLAKE_ACCOUNT="<account_identifier>"
export SNOWFLAKE_USER="<user>"
export SNOWFLAKE_PASSWORD="<password>"
export SNOWFLAKE_ROLE="<role>"
export SNOWFLAKE_WAREHOUSE="<warehouse>"
export SNOWFLAKE_DATABASE="DE_INTEGRATION"
export SNOWFLAKE_SCHEMA="ANALYTICS"
```

## Deliverables and Presentation

- Runnable pipeline.
- Snowflake DDL/DML or setup notes for required database, schemas, stages, and
  tables.
- Implemented Python modules and SQL scripts.
- Tests for extractors, transformations, reject handling, and final output.
- Brief notes on assumptions and how to run the project.
- Brief notes on how the design satisfies idempotency, incremental loading, and
  data quality checks. Be ready to explain these tradeoffs in a follow-up
  technical discussion.
- Brief AI collaboration note if generative AI tools were used.

## AI Policy

Generative AI tools are allowed. Candidates are responsible for everything they
submit and should be able to explain the Python design, SQL transformations,
data quality handling, tests, and tradeoffs in a follow-up technical discussion.
