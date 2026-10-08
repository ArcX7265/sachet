"""Small DB-API boundary: SQLite locally, PostgreSQL for hosted deployments."""
import os
import sqlite3
from pathlib import Path


def postgres_enabled():
    return bool(os.getenv("DATABASE_URL"))


class Record(dict):
    """Preserve the application's named and positional row access."""
    def __getitem__(self, key):
        return tuple(self.values())[key] if isinstance(key, int) else super().__getitem__(key)


def record_factory(cursor):
    names = [column.name for column in cursor.description] if cursor.description else []
    return lambda values: Record(zip(names, values))


class Connection:
    def __init__(self, write=False):
        self.postgres = postgres_enabled()
        if self.postgres:
            import psycopg
            self.raw = psycopg.connect(os.environ["DATABASE_URL"], row_factory=record_factory,
                                       connect_timeout=10, prepare_threshold=None)
            if write:
                # Retain SQLite's serialized write semantics for the small pilot.
                # This transaction lock is shared across all serverless instances.
                self.raw.execute("SELECT pg_advisory_xact_lock(734120261)")
        else:
            if os.getenv("VERCEL") == "1":
                raise RuntimeError("DATABASE_URL is required on Vercel; local SQLite is not durable.")
            path = Path(os.getenv("SACHET_DB_PATH", "data/sachet.sqlite3"))
            path.parent.mkdir(parents=True, exist_ok=True)
            self.raw = sqlite3.connect(path, timeout=20)
            self.raw.row_factory = sqlite3.Row
            self.raw.execute("PRAGMA foreign_keys=ON")
            self.raw.execute("PRAGMA journal_mode=WAL")
            if write:
                self.raw.execute("BEGIN IMMEDIATE")

    def execute(self, sql, params=()):
        # SQL is application-owned; user values always remain bound parameters.
        if self.postgres:
            if not params:
                return self.raw.execute(sql)
            sql = sql.replace("%", "%%").replace("?", "%s")
        return self.raw.execute(sql, params)

    def executescript(self, sql):
        for statement in sql.split(";"):
            if statement.strip():
                self.execute(statement)

    def __enter__(self):
        return self

    def __exit__(self, kind, value, traceback):
        try:
            self.raw.rollback() if kind else self.raw.commit()
        finally:
            self.raw.close()


def db(write=False):
    return Connection(write=write)
