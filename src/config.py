"""Centralized configuration loading for the data integration pipeline.

Responsibilities:
    * Parse the YAML config (``config/dummy.yml``) into a plain dict.
    * Resolve ``${ENV_VAR}`` placeholders against the process environment, so
      secrets are injected at runtime rather than stored in source control.
    * Normalize relative data paths against the project root, making execution
      independent of the current working directory.
    * Expose the active warehouse backend selection.

Design note:
    Credentials (Snowflake account, user, password, ...) are referenced only as
    environment variables and are never hard-coded. Unset variables resolve to
    an empty string, which keeps the local DuckDB test suite runnable without
    any credentials while still documenting exactly where production secrets
    would be supplied.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

# Project root = parent of the ``src`` directory that holds this file.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "dummy.yml"

_ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _expand_env(value: Any) -> Any:
    """Recursively replace ``${VAR}`` placeholders with environment values.

    A missing variable expands to an empty string -- intentional, so that
    loading config never fails just because Snowflake creds are absent.
    """
    if isinstance(value, str):
        return _ENV_PATTERN.sub(lambda m: os.environ.get(m.group(1), ""), value)
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


def load_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load the YAML config, expanding environment-variable placeholders.

    Relative paths in the ``paths`` section are resolved against the project
    root so the pipeline works regardless of the current working directory.
    """
    config_path = Path(config_path)
    with open(config_path, "r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh) or {}

    config = _expand_env(config)

    for key, rel in (config.get("paths") or {}).items():
        config["paths"][key] = str((PROJECT_ROOT / rel).resolve())

    return config


def get_backend() -> str:
    """Which warehouse backend to use: ``duckdb`` (default) or ``snowflake``.

    Controlled by ``WAREHOUSE_BACKEND`` so the same pipeline runs locally on
    DuckDB and, with credentials configured, against Snowflake.
    """
    return os.environ.get("WAREHOUSE_BACKEND", "duckdb").lower()
