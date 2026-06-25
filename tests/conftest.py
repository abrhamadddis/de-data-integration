"""Shared test fixtures.

The pipeline runs once against an in-memory DuckDB backend and the resulting
fact/rejects frames are shared across tests. No credentials are required.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make the project root importable (so ``import src...`` works) regardless of
# where pytest is invoked from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config  # noqa: E402
from src.loaders.duckdb_loader import DuckDBLoader  # noqa: E402
from src.pipeline import run_pipeline  # noqa: E402


@pytest.fixture(scope="session")
def config():
    return load_config()


@pytest.fixture(scope="session")
def pipeline_result(config):
    """Run the full pipeline once on DuckDB; return (fact_df, rejects_df)."""
    warehouse = DuckDBLoader()
    try:
        fact, rejects = run_pipeline(config, warehouse)
    finally:
        warehouse.close()
    return fact, rejects
