"""Shared test fixtures — chiefly the Postgres test database.

Database tests use `upskill_test`, a separate database on the same Postgres
server docker-compose runs for development, so a test run never touches
development data. Once per run it is dropped, recreated empty, and built by
the real Alembic migrations — which means every run also proves the
migrations work from nothing. Before each database test every table is
emptied, so no test can depend on another's leftovers.

If Postgres isn't reachable, database tests are skipped with a visible reason
instead of failing, so the rest of the suite still runs without Docker.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import make_url, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.auth.models  # noqa: F401  (registers every table on Base.metadata,
import app.progress.models  # noqa: F401  which the per-test TRUNCATE reads)
from app.config import settings
from app.db import Base

ROOT = Path(__file__).resolve().parent.parent

# Same server and credentials as development, different database name.
# `render_as_string(hide_password=False)`: a plain str() of a SQLAlchemy URL
# masks the password as ***, which is right for logs but useless for actually
# connecting.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or make_url(
    settings.database_url
).set(database="upskill_test").render_as_string(hide_password=False)

_test_url = make_url(TEST_DATABASE_URL)

# The test database is dropped and recreated on every run. This guard means a
# mistyped TEST_DATABASE_URL can never point that at real data.
if not (_test_url.database or "").endswith("_test"):
    raise RuntimeError(
        f"Refusing to run: TEST_DATABASE_URL names database {_test_url.database!r}, "
        "which doesn't end in '_test'. The test suite drops and recreates its "
        "database, so it will only ever touch one named *_test."
    )


async def _recreate_test_database() -> None:
    # CREATE/DROP DATABASE can't run inside a transaction or while connected
    # to the database itself, hence AUTOCOMMIT via the `postgres` maintenance
    # database. Database names can't be bound parameters, so the name is
    # interpolated — safe because it comes from our own config and has just
    # passed the *_test check above. WITH (FORCE) disconnects anything a
    # previous, crashed run left attached.
    admin = create_async_engine(
        _test_url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
    )
    try:
        async with admin.connect() as conn:
            name = _test_url.database
            await conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
            await conn.execute(text(f'CREATE DATABASE "{name}"'))
    finally:
        await admin.dispose()


def alembic_config() -> Config:
    """Alembic, pointed at the test database instead of the development one."""
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.attributes["database_url"] = TEST_DATABASE_URL
    return cfg


@pytest.fixture(scope="session")
def test_database() -> str:
    """Rebuild the test database once per run, through the real migrations."""
    try:
        asyncio.run(_recreate_test_database())
    except OperationalError:
        pytest.skip(
            f"Postgres not reachable at {_test_url.host}:{_test_url.port} "
            "— run `make db`"
        )
    command.upgrade(alembic_config(), "head")
    return TEST_DATABASE_URL


@pytest.fixture
def alembic_cfg(test_database: str) -> Config:
    return alembic_config()


@pytest.fixture
def anyio_backend() -> str:
    # Async tests (marked `@pytest.mark.anyio`) run on asyncio, the event loop
    # the app itself uses.
    return "asyncio"


@pytest.fixture
async def db_session(test_database: str) -> AsyncIterator[AsyncSession]:
    """A session on the test database, with every table emptied first."""
    engine = create_async_engine(test_database, poolclass=NullPool)
    tables = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    # Same settings as the app's own factory in app/db.py, so tests see the
    # same behaviour the app does.
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()
