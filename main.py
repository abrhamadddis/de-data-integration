"""Command-line entry point that runs the sales integration pipeline end to end.

This module is the thin orchestration layer: it loads configuration, selects a
warehouse backend, delegates the extract/stage/transform/load work to
``src.pipeline``, and writes the resulting fact and reject tables to CSV while
printing a run summary.

Backend selection (via the ``WAREHOUSE_BACKEND`` environment variable):
    * ``duckdb`` (default) -- runs fully locally with no credentials, suitable
      for development and the test suite.
    * ``snowflake`` -- targets a live account; requires the SNOWFLAKE_* env
      vars consumed by :mod:`src.config`.

Usage:
    python main.py
"""

from __future__ import annotations

from pathlib import Path

from src.config import get_backend, load_config
from src.loaders.duckdb_loader import DuckDBLoader
from src.pipeline import format_fact_for_output, run_pipeline

OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "processed" / "output"


def build_warehouse(config: dict):
    """Pick the warehouse backend based on WAREHOUSE_BACKEND (default: duckdb)."""
    backend = get_backend()
    if backend == "snowflake":
        # Imported lazily so the snowflake connector is only required when used.
        from src.loaders.snowflake import SnowflakeLoader

        return SnowflakeLoader(config["snowflake"])
    return DuckDBLoader()


def main() -> None:
    config = load_config()
    warehouse = build_warehouse(config)

    try:
        fact, rejects = run_pipeline(config, warehouse)
    finally:
        warehouse.close()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fact_out = format_fact_for_output(fact)
    fact_path = OUTPUT_DIR / "sales_fact_output.csv"
    rejects_path = OUTPUT_DIR / "sales_rejects_output.csv"
    fact_out.to_csv(fact_path, index=False)
    rejects.to_csv(rejects_path, index=False)

    print(f"Loaded {len(fact)} fact rows  -> {fact_path}")
    print(f"Loaded {len(rejects)} reject rows -> {rejects_path}")
    print("\nSALES_FACT:")
    print(fact_out.to_string(index=False))
    print("\nSALES_REJECTS:")
    print(rejects.to_string(index=False))


if __name__ == "__main__":
    main()
