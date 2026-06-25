"""Abstract extractor contract.

Every source system (core SQL Server, acquired PostgreSQL, ...) is represented
by a subclass that knows how to read its own data but exposes the *same*
``extract()`` method. The pipeline depends on this contract, not on any
concrete source -- so adding a new source means writing one new subclass and
nothing else changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class BaseExtractor(ABC):
    """Contract all extractors must satisfy.

    Attributes:
        source_system: short label identifying the source (e.g. ``"core"``).
            Subclasses must set this; it drives the source-prefixed warehouse
            keys (``core:9001`` / ``acquired:9001``).
    """

    source_system: str = ""

    @abstractmethod
    def extract(self) -> pd.DataFrame:
        """Read the source and return its rows as a DataFrame (raw, untransformed)."""
        raise NotImplementedError
