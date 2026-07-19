"""Reads the real SQLite schema so prompts and guardrails are always in sync with the DB
(no hand-maintained schema string that can drift from the actual tables)."""

import sqlite3
from dataclasses import dataclass, field

from app.config import settings


@dataclass
class TableSchema:
    name: str
    columns: list[str]
    create_sql: str
    sample_rows: list[tuple] = field(default_factory=list)


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(f"file:{settings.sqlite_path}?mode=ro", uri=True)


def get_schema(sample_rows_per_table: int = 3) -> list[TableSchema]:
    connection = _connect()
    try:
        tables = connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()

        schemas = []
        for name, create_sql in tables:
            columns = [row[1] for row in connection.execute(f"PRAGMA table_info({name})")]
            sample_rows = connection.execute(f"SELECT * FROM {name} LIMIT {sample_rows_per_table}").fetchall()
            schemas.append(TableSchema(name=name, columns=columns, create_sql=create_sql, sample_rows=sample_rows))
        return schemas
    finally:
        connection.close()


def allowed_tables_and_columns() -> dict[str, set[str]]:
    """Table -> set of column names, used by the SQL guardrail to reject unknown identifiers."""
    return {table.name: set(table.columns) for table in get_schema()}


def render_table_info(schemas: list[TableSchema] | None = None) -> str:
    """Renders a `{table_info}` block similar to LangChain's SQLDatabase.table_info, for prompts."""
    schemas = schemas if schemas is not None else get_schema()
    blocks = []
    for table in schemas:
        header = f"{table.create_sql}\n"
        if table.sample_rows:
            rows_str = "\n".join(str(row) for row in table.sample_rows)
            header += f"\n/*\n{len(table.sample_rows)} rows from {table.name} table:\n{', '.join(table.columns)}\n{rows_str}\n*/\n"
        blocks.append(header)
    return "\n".join(blocks)
