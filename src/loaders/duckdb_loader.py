"""DuckDB implementation of the warehouse boundary.

DuckDB is a local, embedded SQL engine that needs no server or credentials, so
it stands in for Snowflake in the local pipeline and the test suite. Its SQL
dialect is close enough to Snowflake that the transformation scripts read almost
identically (differences are noted in the .sql files).
"""

from __future__ import annotations

import duckdb
import pandas as pd

from .base_loader import WarehouseLoader


class DuckDBLoader(WarehouseLoader):
    """WarehouseLoader backed by DuckDB; in-memory by default, file if a path is given."""

    def __init__(self, database: str = ":memory:"):
        # ":memory:" is ephemeral (gone on close); pass a path to persist/inspect.
        self.connection = duckdb.connect(database)

    def create_schemas(self, schemas: list[str]) -> None:
        for schema in schemas:
            self.connection.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    def stage_dataframe(self, table: str, df: pd.DataFrame) -> None:
        # Register the DataFrame and materialize it as a table, fully replacing
        # any prior contents so staging is a clean full load each run.
        self.connection.register("_staging_df", df)
        self.connection.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM _staging_df")
        self.connection.unregister("_staging_df")

    def execute_sql(self, sql_text: str) -> None:
        self.connection.execute(sql_text)

    def fetch_dataframe(self, query: str) -> pd.DataFrame:
        return self.connection.execute(query).fetchdf()

    def close(self) -> None:
        self.connection.close()
