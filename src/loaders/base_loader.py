"""Warehouse boundary as an interface.

The pipeline talks only to ``WarehouseLoader`` -- never directly to Snowflake.
This is the seam that lets us run the exact same pipeline against DuckDB locally
(no credentials) and Snowflake in production by swapping the implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class WarehouseLoader(ABC):
    """The five operations the pipeline needs from any warehouse: create
    schemas, stage a frame, run SQL, fetch results, and close. Concrete backends
    (DuckDB, Snowflake) supply the implementations."""

    @abstractmethod
    def create_schemas(self, schemas: list[str]) -> None:
        """Ensure the given schemas (e.g. RAW, ANALYTICS) exist."""

    @abstractmethod
    def stage_dataframe(self, table: str, df: pd.DataFrame) -> None:
        """Replace ``table`` with the contents of ``df`` (full load of staging)."""

    @abstractmethod
    def execute_sql(self, sql_text: str) -> None:
        """Execute one or more SQL statements that return no rows."""

    @abstractmethod
    def fetch_dataframe(self, query: str) -> pd.DataFrame:
        """Run a query and return the result as a DataFrame."""

    def close(self) -> None:
        """Release the connection. Override if the backend needs cleanup."""
