"""Safe read-only SQL access for the agent.

Safety layers (an LLM writes these queries, so never trust them blindly):
1. Only a single SELECT / WITH statement is accepted.
2. The database is opened in read-only mode, so even a missed write is refused by SQLite.
3. Results are capped at MAX_ROWS so a bad query cannot flood the LLM context.
Errors are returned as text instead of raised: the agent reads them and fixes its query.
"""
import re
import sqlite3
from pathlib import Path

MAX_ROWS = 50
_FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|attach|pragma|vacuum)\b", re.I)


def get_schema(db_path: Path) -> str:
    """CREATE statements of all tables, including the comments written in build_db.py."""
    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
        rows = conn.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND sql IS NOT NULL").fetchall()
    return "\n\n".join(r[0] for r in rows)


def validate_query(query: str) -> str | None:
    """Return an error message if the query is not allowed, else None."""
    stripped = query.strip().rstrip(";").strip()
    if not stripped:
        return "ERROR: empty query."
    if ";" in stripped:
        return "ERROR: only one SQL statement is allowed."
    if not re.match(r"^(select|with)\b", stripped, re.I):
        return "ERROR: only SELECT queries are allowed."
    if _FORBIDDEN.search(stripped):
        return "ERROR: this query contains a forbidden keyword (read-only access)."
    return None


def run_query(query: str, db_path: Path) -> str:
    """Execute a read-only query and return the result as a small text table."""
    error = validate_query(query)
    if error:
        return error
    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
            cursor = conn.execute(query.strip().rstrip(";"))
            columns = [d[0] for d in cursor.description]
            rows = cursor.fetchmany(MAX_ROWS + 1)
    except sqlite3.Error as exc:
        return f"ERROR: {exc}. Check table and column names against the schema and try again."

    if not rows:
        return "The query returned no rows. Check the spelling of team/player names (English names, e.g. 'United States')."

    truncated = len(rows) > MAX_ROWS
    lines = [" | ".join(columns)] + [" | ".join(str(v) for v in row) for row in rows[:MAX_ROWS]]
    if truncated:
        lines.append(f"... (truncated to {MAX_ROWS} rows, add LIMIT or aggregate)")
    return "\n".join(lines)
