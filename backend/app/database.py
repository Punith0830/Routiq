"""Local database foundation. No unapproved habit policies are calculated here."""
import sqlite3
from pathlib import Path


def initialize(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version > 3:
            raise RuntimeError("Unsupported database schema version")
        if version == 0:
            connection.execute("CREATE TABLE app_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            connection.execute("INSERT INTO app_metadata VALUES (?, ?)", ("application", "routiq"))
            connection.execute("PRAGMA user_version = 1")
            version = 1
        if version == 1:
            connection.execute("CREATE TABLE habits (id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL, created_at TEXT NOT NULL, start_date TEXT NOT NULL)")
            connection.execute("CREATE TABLE completions (habit_id TEXT NOT NULL REFERENCES habits(id), day TEXT NOT NULL, PRIMARY KEY(habit_id, day))")
            connection.execute("PRAGMA user_version = 2")
            version = 2
        if version == 2:
            for field in ('reason', 'small_action', 'cue'):
                connection.execute(f"ALTER TABLE habits ADD COLUMN {field} TEXT NOT NULL DEFAULT ''")
            connection.execute("PRAGMA user_version = 3")


def available(path: Path) -> bool:
    try:
        with sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True) as connection:
            return connection.execute("SELECT value FROM app_metadata WHERE key = ?", ("application",)).fetchone() == ("routiq",)
    except sqlite3.Error:
        return False
