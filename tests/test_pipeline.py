"""End-to-end test: pipeline output must match the expected fixtures exactly."""

from __future__ import annotations

import pandas as pd
import pandas.testing as pdt

from src.config import load_config
from src.pipeline import (
    FACT_COLUMNS,
    REJECT_COLUMNS,
    format_fact_for_output,
)


def _as_sorted_strings(df: pd.DataFrame, columns: list[str], sort_by: list[str]) -> pd.DataFrame:
    """Cast all columns to str and sort, so comparison ignores dtype/row order."""
    out = df[columns].astype(str)
    return out.sort_values(sort_by).reset_index(drop=True)


def _read_expected(path: str) -> pd.DataFrame:
    # dtype=str + keep_default_na=False so "" stays "" and nothing is coerced.
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def test_fact_matches_expected(pipeline_result):
    fact, _ = pipeline_result
    config = load_config()

    actual = _as_sorted_strings(
        format_fact_for_output(fact), FACT_COLUMNS, ["warehouse_transaction_id"]
    )
    expected = _as_sorted_strings(
        _read_expected(config["paths"]["expected_sales_fact"]),
        FACT_COLUMNS,
        ["warehouse_transaction_id"],
    )

    pdt.assert_frame_equal(actual, expected)


def test_rejects_match_expected(pipeline_result):
    _, rejects = pipeline_result
    config = load_config()

    sort_by = ["source_system", "source_transaction_id"]
    actual = _as_sorted_strings(rejects, REJECT_COLUMNS, sort_by)
    expected = _as_sorted_strings(
        _read_expected(config["paths"]["expected_rejects"]), REJECT_COLUMNS, sort_by
    )

    pdt.assert_frame_equal(actual, expected)


def test_row_counts(pipeline_result):
    fact, rejects = pipeline_result
    assert len(fact) == 7
    assert len(rejects) == 4


def test_pipeline_is_idempotent(config):
    """Running the pipeline twice on the same backend yields identical results."""
    from src.loaders.duckdb_loader import DuckDBLoader
    from src.pipeline import run_pipeline

    warehouse = DuckDBLoader()
    try:
        fact1, rejects1 = run_pipeline(config, warehouse)
        fact2, rejects2 = run_pipeline(config, warehouse)
    finally:
        warehouse.close()

    assert len(fact1) == len(fact2) == 7
    assert len(rejects1) == len(rejects2) == 4
