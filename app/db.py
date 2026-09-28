"""Database engine and session management.

Cross-cutting, so it lives directly under `app/` rather than inside a feature
folder — the same rule `config.py`, `logging.py`, and `templates.py` follow.
Every feature that stores anything needs a session from here.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Every constraint and index gets a predictable name from these patterns,
# instead of whatever Postgres invents. A later migration that drops or alters
# a constraint has to name it exactly — with invented names, that means looking
# it up, and the invented name can differ between databases, so a migration
# that works locally can fail on the server.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """The shared declarative base every model inherits from.

    Its `.metadata` is the single registry of every table in the app, which
    is what Alembic compares against the live database to work out what a
    migration needs to change. Models live in their own feature folders
    (`app/auth/`, `app/progress/`), so this has to sit somewhere common —
    and each model module must be imported before autogenerate runs, or its
    table is absent from the registry and Alembic cheerfully generates a
    migration that drops it. `migrations/env.py` does that importing.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    # Columns the *database* fills in (`server_default=func.now()`,
    # `onupdate=func.now()`) are unknown to SQLAlchemy until it asks. It asks
    # automatically after an INSERT, but not after an UPDATE — it just marks
    # the value unknown, so the next plain `obj.updated_at` read goes to the
    # database. In async code that's forbidden and raises `MissingGreenlet`.
    # This makes it fetch those values back in the same round trip on UPDATE
    # too, so they're never left unknown. Inherited by every model; a model
    # that sets its own `__mapper_args__` must repeat it.
    __mapper_args__ = {"eager_defaults": True}


# Creating the engine opens no connection — it builds a pool that connects
# lazily, on first use. Importing this module therefore stays cheap and does
# not require Postgres to be running, which matters because `app.main`
# imports the whole app graph at startup.
engine = create_async_engine(settings.database_url)

# `expire_on_commit=False` matters specifically for async. The default marks
# every loaded attribute stale after a commit, so the next attribute read
# quietly re-fetches it — and in async that means IO from a plain attribute
# access, somewhere the code doesn't look like it's touching the database.
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """One session per request, closed when the request ends.

    Used as a FastAPI dependency: a route takes
    `session: Annotated[AsyncSession, Depends(get_session)]` and gets its own
    session, rather than sharing one — a session holds per-transaction state,
    so sharing across concurrent requests would interleave their work.
    """
    async with session_factory() as session:
        yield session
