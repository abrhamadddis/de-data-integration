"""Generic CSV extractor for reference/lookup data (e.g. exchange rates).

Reference data isn't a "source system", so it has no source-system prefix; it
just needs to be read and staged. Reusing the same ``extract()`` contract keeps
the staging step uniform.
"""

from __future__ import annotations

import pandas as pd

from .base_extractor import BaseExtractor


class CsvExtractor(BaseExtractor):
    """Reads an arbitrary CSV fixture as text."""

    def __init__(self, source_path: str, source_system: str = "reference"):
        self.source_path = source_path
        self.source_system = source_system

    def extract(self) -> pd.DataFrame:
        return pd.read_csv(self.source_path, dtype=str).fillna("")
