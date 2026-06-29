"""Pipeline orchestration, independent of the warehouse backend.

``run_pipeline`` wires extractors -> staging -> SQL transforms -> fact/rejects
and returns the results as DataFrames. Both ``main.py`` (DuckDB or Snowflake)
and the test suite (DuckDB) call this same function, so what is tested is
exactly what runs.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .extractors.csv_extractor import CsvExtractor
from .extractors.postgres import PostgresExtractor
from .extractors.sqlserver import SQLServerExtractor
from .loaders.base_loader import WarehouseLoader
from .loaders.staging import StagingLoader
from .transformers.sql_runner import SqlRunner

SQL_DIR = Path(__file__).resolve().parent / "sql"
SCHEMAS = ["RAW", "ANALYTICS"]
SQL_FILES = ["staging_core.sql", "staging_acquired.sql", "warehouse_merge.sql"]

FACT_COLUMNS = [
    "source_system",
    "source_transaction_id",
    "warehouse_transaction_id",
    "checkout_timestamp",
    "customer_id",
    "customer_country",
    "sku",
    "gross_amount_usd",
    "tax_amount_usd",
    "is_refunded",
]
REJECT_COLUMNS = ["source_system", "source_transaction_id", "reject_reason"]

# Order core rows before acquired (source_system DESC) to match the expected
# fixtures and give a clean, deterministic diff.
_FACT_QUERY = (
    "SELECT " + ", ".join(FACT_COLUMNS) + " FROM ANALYTICS.SALES_FACT "
    "ORDER BY source_system DESC, source_transaction_id"
)
_REJECT_QUERY = (
    "SELECT " + ", ".join(REJECT_COLUMNS) + " FROM ANALYTICS.SALES_REJECTS "
    "ORDER BY source_system DESC, source_transaction_id"
)


def run_pipeline(config: dict, warehouse: WarehouseLoader) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run extract -> stage -> transform -> load against the given backend.

    Extracts the three CSV sources, stages them into RAW.STG_* tables, runs the
    SQL transform scripts in order, and returns the resulting SALES_FACT and
    SALES_REJECTS tables as (fact, rejects) DataFrames.
    """
    paths = config["paths"]

    core_df = SQLServerExtractor(paths["sqlserver_sales"]).extract()
    acquired_df = PostgresExtractor(paths["postgres_sales"]).extract()
    rates_df = CsvExtractor(paths["exchange_rates"]).extract()

    warehouse.create_schemas(SCHEMAS)
    StagingLoader(warehouse).stage_sources(core_df, acquired_df, rates_df)

    runner = SqlRunner(warehouse, SQL_DIR)
    for sql_file in SQL_FILES:
        runner.run_file(sql_file)

    fact = warehouse.fetch_dataframe(_FACT_QUERY)
    rejects = warehouse.fetch_dataframe(_REJECT_QUERY)
    return fact, rejects


def format_fact_for_output(fact: pd.DataFrame) -> pd.DataFrame:
    """Normalize fact values to the text form used by the expected fixture.

    Stringifies timestamps, blanks missing countries, fixes amounts to two
    decimals, and lowercases the refund flag -- presentation only, no data change.
    """
    out = fact.copy()
    out["checkout_timestamp"] = out["checkout_timestamp"].astype(str)
    out["customer_country"] = out["customer_country"].fillna("")
    out["gross_amount_usd"] = out["gross_amount_usd"].map(lambda v: f"{v:.2f}")
    out["tax_amount_usd"] = out["tax_amount_usd"].map(lambda v: f"{v:.2f}")
    out["is_refunded"] = out["is_refunded"].map(lambda v: "true" if v else "false")
    return out[FACT_COLUMNS]
