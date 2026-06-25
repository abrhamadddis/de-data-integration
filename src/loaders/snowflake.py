"""Snowflake implementation of the warehouse boundary.

This is the production target and the single place Snowflake credentials are
configured -- they arrive via ``config/dummy.yml`` which reads them from
environment variables (``SNOWFLAKE_ACCOUNT`` etc.). Nothing here is required for
the local test suite, which uses :class:`~src.loaders.duckdb_loader.DuckDBLoader`.

The import of ``snowflake.connector`` is deferred to ``__init__`` so the package
can be imported (and DuckDB-based tests can run) even if the connector or
credentials are unavailable.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .base_loader import WarehouseLoader


class SnowflakeLoader(WarehouseLoader):
    """Loads and transforms data in a live Snowflake account.

    Args:
        snowflake_config: the ``snowflake`` section of the loaded config, e.g.
            ``account``, ``user``, ``password``, ``role``, ``warehouse``,
            ``database``. Credentials are expected to be already expanded from
            environment variables by :func:`src.config.load_config`.
    """

    def __init__(self, snowflake_config: dict[str, Any]):
        import snowflake.connector  # deferred: not needed for local/DuckDB runs

        self.config = snowflake_config
        self.database = snowflake_config.get("database", "DE_INTEGRATION")
        self.connection = snowflake.connector.connect(
            account=snowflake_config.get("account"),
            user=snowflake_config.get("user"),
            password=snowflake_config.get("password"),
            role=snowflake_config.get("role") or None,
            warehouse=snowflake_config.get("warehouse") or None,
            database=self.database,
        )

    def create_schemas(self, schemas: list[str]) -> None:
        cur = self.connection.cursor()
        try:
            for schema in schemas:
                cur.execute(f"CREATE SCHEMA IF NOT EXISTS {self.database}.{schema}")
        finally:
            cur.close()

    def stage_dataframe(self, table: str, df: pd.DataFrame) -> None:
        # write_pandas handles the PUT-to-stage + COPY INTO under the hood, which
        # is the efficient bulk path for loading a DataFrame into Snowflake.
        from snowflake.connector.pandas_tools import write_pandas

        schema, _, table_name = table.partition(".")
        write_pandas(
            self.connection,
            df,
            table_name=table_name,
            database=self.database,
            schema=schema or None,
            auto_create_table=True,
            overwrite=True,
        )

    def execute_sql(self, sql_text: str) -> None:
        cur = self.connection.cursor()
        try:
            # execute_string runs a multi-statement script in one call.
            cur.execute_string(sql_text)
        finally:
            cur.close()

    def fetch_dataframe(self, query: str) -> pd.DataFrame:
        cur = self.connection.cursor()
        try:
            cur.execute(query)
            return cur.fetch_pandas_all()
        finally:
            cur.close()

    def close(self) -> None:
        self.connection.close()
