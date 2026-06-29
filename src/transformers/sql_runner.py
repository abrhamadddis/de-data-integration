"""Reusable SQL script runner.

Reads a ``.sql`` file from disk and executes it against any
:class:`~src.loaders.base_loader.WarehouseLoader`. Keeping the transformation
logic in standalone SQL files (run by this thin runner) is what satisfies the
"Snowflake-native transformations in src/sql/" requirement.
"""

from __future__ import annotations

from pathlib import Path

from ..loaders.base_loader import WarehouseLoader


class SqlRunner:
    """Runs .sql files from a directory against a warehouse backend.

    Dialect-agnostic: it only reads files and forwards statements to the
    backend's ``execute_sql``; the SQL itself carries all transformation logic.
    """

    def __init__(self, warehouse: WarehouseLoader, sql_dir: str | Path):
        self.warehouse = warehouse
        self.sql_dir = Path(sql_dir)

    def run_file(self, filename: str) -> None:
        """Execute ``sql_dir/filename`` as a script."""
        sql_text = (self.sql_dir / filename).read_text(encoding="utf-8")
        self.run_script(sql_text)

    def run_script(self, sql_text: str) -> None:
        """Execute a SQL script, statement by statement.

        Line (``--``) comments are stripped first, then statements are split on
        ``;``. Stripping comments avoids a semicolon *inside* a comment being
        mistaken for a statement separator. This is adequate here because the
        scripts contain no ``--`` or ``;`` inside string literals.
        """
        for statement in self._strip_comments(sql_text).split(";"):
            if statement.strip():
                self.warehouse.execute_sql(statement)

    @staticmethod
    def _strip_comments(sql_text: str) -> str:
        """Remove ``--`` line comments from a SQL script."""
        lines = []
        for line in sql_text.splitlines():
            comment_start = line.find("--")
            if comment_start != -1:
                line = line[:comment_start]
            lines.append(line)
        return "\n".join(lines)
