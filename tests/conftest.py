import os

import pytest

from reportkit.db import get_engine
from reportkit.web import app


@pytest.fixture(scope="session")
def engine():
    """The Sakila database: PostgreSQL when DATABASE_URL is set (as in CI), otherwise the local SQLite copy."""
    eng = get_engine(os.environ.get("DATABASE_URL"))
    yield eng
    eng.dispose()


@pytest.fixture
def client(engine):
    from fastapi.testclient import TestClient

    app.state.engine = engine
    yield TestClient(app)
    app.state.engine = None
