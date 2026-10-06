"""The `users` table's rules, checked against the real test database."""

import asyncio
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User

pytestmark = [pytest.mark.db, pytest.mark.anyio]


def new_user(github_id: int = 1001, login: str = "kanubir") -> User:
    return User(
        github_id=github_id, login=login, avatar_url="https://avatars.example/x"
    )


async def test_user_round_trips_with_generated_and_database_filled_values(
    db_session: AsyncSession,
):
    user = new_user()
    db_session.add(user)
    await db_session.commit()

    assert isinstance(user.id, uuid.UUID)  # our own ID, generated in Python
    assert user.created_at is not None  # filled in by the database
    assert user.updated_at is not None

    found = await db_session.scalar(select(User).where(User.github_id == 1001))
    assert found is not None
    assert found.id == user.id


async def test_updated_at_moves_forward_on_update(db_session: AsyncSession):
    # Also guards `eager_defaults=True` on Base: without it, reading
    # `updated_at` after an update raises MissingGreenlet in async code.
    user = new_user()
    db_session.add(user)
    await db_session.commit()
    before = user.updated_at

    await asyncio.sleep(0.01)
    user.login = "kanubir-renamed"
    await db_session.commit()

    assert user.updated_at > before


async def test_same_github_id_twice_is_refused(db_session: AsyncSession):
    db_session.add(new_user(github_id=1001, login="kanubir"))
    await db_session.commit()

    db_session.add(new_user(github_id=1001, login="someone-else"))
    with pytest.raises(IntegrityError, match="uq_users_github_id"):
        await db_session.commit()


async def test_reused_login_on_a_different_account_is_allowed(db_session: AsyncSession):
    # GitHub usernames can be renamed and later reclaimed by someone else, so
    # `login` is deliberately not unique — only `github_id` identifies a person.
    db_session.add(new_user(github_id=1001, login="kanubir"))
    db_session.add(new_user(github_id=2002, login="kanubir"))
    await db_session.commit()

    logins = await db_session.scalars(select(User.login))
    assert list(logins) == ["kanubir", "kanubir"]
