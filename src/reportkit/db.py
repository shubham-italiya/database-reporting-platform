"""Database connection, the sample database, and the SQL files.

The database is chosen with DATABASE_URL (any SQLAlchemy URL). Without it, a local SQLite copy of the
Sakila sample database is used and built on first use.

Sakila: the classic DVD-rental sample database (MySQL AB), as ported to SQLite and PostgreSQL by jOOQ:
https://github.com/jOOQ/sakila, BSD 2-Clause licence.
"""
from __future__ import annotations

import os
import re
import sqlite3
import urllib.request
from functools import lru_cache

from sqlalchemy import Engine, create_engine

from .paths import DATA_DIR, SQL_DIR

SAKILA = "https://raw.githubusercontent.com/jOOQ/sakila/main/sqlite-sakila-db/"
SQLITE_FILE = DATA_DIR / "sakila.db"


def build_sqlite(path=SQLITE_FILE) -> None:
    """Download the Sakila scripts (~8.5 MB) and build a SQLite database."""
    DATA_DIR.mkdir(exist_ok=True)
    scripts = []
    for name in ("sqlite-sakila-schema.sql", "sqlite-sakila-insert-data.sql"):
        local = DATA_DIR / name
        if not local.exists():
            urllib.request.urlretrieve(SAKILA + name, local)
        scripts.append(local.read_text(encoding="utf-8"))
    tmp = path.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    with sqlite3.connect(tmp) as conn:
        for script in scripts:
            conn.executescript(script)
    tmp.replace(path)


def get_engine(url: str | None = None) -> Engine:
    url = url or os.environ.get("DATABASE_URL")
    if not url:
        if not SQLITE_FILE.exists():
            build_sqlite()
        url = f"sqlite:///{SQLITE_FILE}"
    return create_engine(url)


@lru_cache
def sql(name: str) -> str:
    """Read sql/<name>.sql without comments (SQLAlchemy would read ':name' in a comment as a parameter)."""
    text = (SQL_DIR / f"{name}.sql").read_text()
    return re.sub(r"--[^\n]*", "", text).strip().rstrip(";")
