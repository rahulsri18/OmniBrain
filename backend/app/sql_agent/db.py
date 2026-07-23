from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from ..logger import logger


class ReadOnlySQLQueryError(ValueError):
    """Raised when a query is not allowed in read-only mode."""


class ReadOnlySQLDatabase:
    """Execute read-only SQLite queries and return rows as dictionaries."""

    _WRITE_ACTIONS = {
        sqlite3.SQLITE_INSERT,
        sqlite3.SQLITE_UPDATE,
        sqlite3.SQLITE_DELETE,
        sqlite3.SQLITE_ALTER_TABLE,
        sqlite3.SQLITE_DROP_TABLE,
        sqlite3.SQLITE_DROP_INDEX,
        sqlite3.SQLITE_DROP_TRIGGER,
        sqlite3.SQLITE_DROP_VIEW,
        sqlite3.SQLITE_CREATE_TABLE,
        sqlite3.SQLITE_CREATE_INDEX,
        sqlite3.SQLITE_CREATE_TRIGGER,
        sqlite3.SQLITE_CREATE_VIEW,
        sqlite3.SQLITE_CREATE_TEMP_TABLE,
        sqlite3.SQLITE_CREATE_TEMP_INDEX,
        sqlite3.SQLITE_CREATE_TEMP_TRIGGER,
        sqlite3.SQLITE_CREATE_TEMP_VIEW,
        sqlite3.SQLITE_TRANSACTION,
        sqlite3.SQLITE_ATTACH,
        sqlite3.SQLITE_DETACH,
        sqlite3.SQLITE_REINDEX,
        sqlite3.SQLITE_ANALYZE,
    }

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        self._ensure_database_exists()
        self._validate_read_only_statement(sql)
        self._reject_multiple_statements(sql)

        logger.info("Executing read-only SQL query against %s", self.db_path)

        try:
            with sqlite3.connect(
                f"{self.db_path.resolve().as_uri()}?mode=ro",
                uri=True,
            ) as connection:
                connection.row_factory = sqlite3.Row
                connection.set_authorizer(self._authorizer)

                cursor = connection.execute(sql)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as exc:
            logger.error("SQLite query failed for %s: %s", self.db_path, exc)
            raise RuntimeError("Failed to execute SQLite query.") from exc

    def execute_one(self, sql: str) -> dict[str, Any] | None:
        rows = self.execute_query(sql)
        return rows[0] if rows else None

    def _ensure_database_exists(self) -> None:
        if not self.db_path.exists():
            raise FileNotFoundError(f"SQLite database not found: {self.db_path}")

    def _validate_read_only_statement(self, sql: str) -> None:
        statement = sql.lstrip()
        if not statement:
            raise ReadOnlySQLQueryError("SQL query cannot be empty.")

        first_token = statement.split(None, 1)[0].upper()
        if first_token not in {"SELECT", "WITH", "PRAGMA", "EXPLAIN"}:
            raise ReadOnlySQLQueryError("Only read-only SQL statements are allowed.")

    def _reject_multiple_statements(self, sql: str) -> None:
        stripped_sql = sql.strip()
        if not stripped_sql:
            return

        if stripped_sql.endswith(";"):
            stripped_sql = stripped_sql[:-1].rstrip()

        if ";" in stripped_sql:
            raise ReadOnlySQLQueryError("Multiple SQL statements are not allowed.")

    def _authorizer(
        self,
        action_code: int,
        _param1: str | None,
        _param2: str | None,
        _db_name: str | None,
        _trigger_name: str | None,
    ) -> int:
        if action_code in self._WRITE_ACTIONS:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
