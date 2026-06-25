"""Acquired sales extractor (PostgreSQL source).

Same contract as the core extractor; locally backed by a CSV fixture. The
acquired source stores customer ids in a plain column (no JSON), prices in
mixed currencies, and dates in mixed formats -- all handled downstream in SQL.
"""

from __future__ import annotations

import pandas as pd

from .base_extractor import BaseExtractor


class PostgresExtractor(BaseExtractor):
    """Extracts raw acquired sales from the PostgreSQL mock CSV."""

    source_system = "acquired"

    def __init__(self, source_path: str):
        self.source_path = source_path

    def extract(self) -> pd.DataFrame:
        return pd.read_csv(self.source_path, dtype=str).fillna("")
