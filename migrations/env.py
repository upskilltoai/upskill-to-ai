import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

import app.auth.models  # noqa: F401  (registers User on Base.metadata)
import app.progress.models  # noqa: F401  (registers StepCompletion)
from app.config import settings
from app.db import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Autogenerate works by comparing `Base.metadata` — the registry of every
# table the app defines — against the live database. A model class only
# registers itself when its module is imported, so every model module must be
# imported here. Miss one and autogenerate doesn't just skip it: the table is
# absent from the registry, so Alembic concludes it was deleted and writes a
# migration that drops it.
#
# Model modules are imported at the top of this file — add one import per new
# models module. The `noqa: F401` stops the linter deleting an import that
# looks unused but exists purely for this side effect.
target_metadata = Base.metadata


def engine_config() -> dict[str, str]:
    """The engine settings from alembic.ini, with our real database URL.

    The URL comes from `app.config.settings`, so there is exactly one place
    it's configured and no credentials sit in a committed .ini file. It's
    injected into the already-parsed dict rather than written back through
    `set_main_option`, because that path runs the value through ConfigParser
    interpolation, where a `%` in a password would be read as a substitution
    and either fail or silently mangle the URL.
    """
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = settings.database_url
    return section


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # NullPool: a migration run is a short-lived process doing one job, so
    # pooling connections it will never reuse just delays exit.
    connectable = async_engine_from_config(
        engine_config(),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
