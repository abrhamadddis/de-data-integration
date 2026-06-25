"""Unit tests for the SQL runner and the DuckDB warehouse loader."""

from __future__ import annotations

import pandas as pd

from src.loaders.duckdb_loader import DuckDBLoader
from src.transformers.sql_runner import SqlRunner


def test_loader_stage_and_fetch_roundtrip():
    """A staged DataFrame can be read back through the loader."""
    warehouse = DuckDBLoader()
    try:
        warehouse.create_schemas(["RAW"])
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        warehouse.stage_dataframe("RAW.SAMPLE", df)

        result = warehouse.fetch_dataframe("SELECT * FROM RAW.SAMPLE ORDER BY a")
        assert list(result["a"]) == [1, 2]
        assert list(result["b"]) == ["x", "y"]
    finally:
        warehouse.close()


def test_sql_runner_executes_multiple_statements(tmp_path):
    """SqlRunner runs each statement in a multi-statement .sql file."""
    sql_file = tmp_path / "script.sql"
    sql_file.write_text(
        "CREATE SCHEMA IF NOT EXISTS RAW;\n"
        "CREATE TABLE RAW.T AS SELECT 1 AS n;\n"
        "INSERT INTO RAW.T VALUES (2);"
    )

    warehouse = DuckDBLoader()
    try:
        runner = SqlRunner(warehouse, tmp_path)
        runner.run_file("script.sql")

        total = warehouse.fetch_dataframe("SELECT SUM(n) AS s FROM RAW.T")
        assert int(total["s"][0]) == 3
    finally:
        warehouse.close()
