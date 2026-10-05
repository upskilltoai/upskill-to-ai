"""The migrations themselves: they build the schema, match the models, and reverse."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Base

pytestmark = pytest.mark.db


@pytest.mark.anyio
async def test_migrations_build_every_model_table(db_session: AsyncSession):
    # The test database started empty this run; only the migrations put
    # tables in it. So this also proves they run clean from nothing.
    rows = await db_session.execute(
        text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        )
    )
    tables = {row.table_name for row in rows}
    assert tables == {table.name for table in Base.metadata.sorted_tables} | {
        "alembic_version"
    }


def test_models_match_migrations(alembic_cfg: Config):
    # `alembic check` as a test: fails if a model changed without a migration.
    command.check(alembic_cfg)


def test_migrations_reverse_cleanly(alembic_cfg: Config):
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")
    command.check(alembic_cfg)
