"""Core sales extractor (SQL Server source).

Locally this reads a CSV fixture, but the public surface (``extract()``) is the
same one a live SQL Server connection would expose -- so swapping the fixture
for a real ``pyodbc``/SQLAlchemy query later touches only this class.
"""

from __future__ import annotations

import pandas as pd

from .base_extractor import BaseExtractor


class SQLServerExtractor(BaseExtractor):
    """Extracts raw core sales from the SQL Server mock CSV."""

    source_system = "core"

    def __init__(self, source_path: str):
        self.source_path = source_path

    def extract(self) -> pd.DataFrame:
        # dtype=str keeps every column as text so nothing is silently coerced
        # before the SQL transformations decide how to parse it (JSON, dates,
        # numeric amounts, the 0/1 refund flag).
        return pd.read_csv(self.source_path, dtype=str).fillna("")
