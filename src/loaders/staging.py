"""Staging loader: moves extracted source frames into the RAW staging tables.

It is backend-agnostic -- it delegates the actual writes to whatever
:class:`~src.loaders.base_loader.WarehouseLoader` it is given (DuckDB or
Snowflake), so the staging step is identical in tests and production.
"""

from __future__ import annotations

import pandas as pd

from .base_loader import WarehouseLoader

RAW_SCHEMA = "RAW"

STG_CORE = f"{RAW_SCHEMA}.STG_CORE_SALES"
STG_ACQUIRED = f"{RAW_SCHEMA}.STG_ACQUIRED_SALES"
STG_EXCHANGE_RATES = f"{RAW_SCHEMA}.STG_EXCHANGE_RATES"


class StagingLoader:
    """Owns the RAW.STG_* table names and loads each source into them.

    Holds no database logic of its own -- it delegates every write to the
    injected ``WarehouseLoader``, so staging behaves identically on any backend.
    """

    def __init__(self, warehouse: WarehouseLoader):
        self.warehouse = warehouse

    def stage_sources(
        self,
        core_df: pd.DataFrame,
        acquired_df: pd.DataFrame,
        exchange_rates_df: pd.DataFrame,
    ) -> None:
        """Land the three raw inputs as RAW.STG_* tables (full replace)."""
        self.warehouse.stage_dataframe(STG_CORE, core_df)
        self.warehouse.stage_dataframe(STG_ACQUIRED, acquired_df)
        self.warehouse.stage_dataframe(STG_EXCHANGE_RATES, exchange_rates_df)
