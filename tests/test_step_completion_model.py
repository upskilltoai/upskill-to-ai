"""The `step_completions` table's rules, checked against the real test database."""

import uuid

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.progress.models import StepCompletion

pytestmark = [pytest.mark.db, pytest.mark.anyio]

STEP = uuid.uuid4()


@pytest.fixture
async def user_id(db_session: AsyncSession) -> uuid.UUID:
    user = User(github_id=1001, login="kanubir", avatar_url="https://avatars.example/x")
    db_session.add(user)
    await db_session.commit()
    # Returned as a plain value on purpose: a rollback (which several tests
    # below trigger) marks every loaded object unknown, so reading `user.id`
    # afterwards would raise MissingGreenlet in async code.
    return user.id


async def count_completions(session: AsyncSession) -> int:
    return await session.scalar(select(func.count()).select_from(StepCompletion)) or 0


async def test_completion_is_stored_with_a_database_filled_time(
    db_session: AsyncSession, user_id: uuid.UUID
):
    completion = StepCompletion(user_id=user_id, step_uuid=STEP)
    db_session.add(completion)
    await db_session.commit()

    assert completion.completed_at is not None
    assert await count_completions(db_session) == 1


async def test_completing_the_same_step_twice_is_refused(
    db_session: AsyncSession, user_id: uuid.UUID
):
    db_session.add(StepCompletion(user_id=user_id, step_uuid=STEP))
    await db_session.commit()

    db_session.add(StepCompletion(user_id=user_id, step_uuid=STEP))
    with pytest.raises(IntegrityError, match="pk_step_completions"):
        await db_session.commit()


async def test_completion_for_a_learner_who_does_not_exist_is_refused(
    db_session: AsyncSession,
):
    db_session.add(StepCompletion(user_id=uuid.uuid4(), step_uuid=STEP))
    with pytest.raises(IntegrityError, match="fk_step_completions_user_id_users"):
        await db_session.commit()


async def test_step_uuid_is_not_checked_by_the_database(
    db_session: AsyncSession, user_id: uuid.UUID
):
    # By design: steps live in curriculum.json, not in the database, so there's
    # nothing for a foreign key to point at. Any uuid is accepted here — what
    # keeps it meaningful is the rule that a published step's uuid never changes.
    db_session.add(StepCompletion(user_id=user_id, step_uuid=uuid.uuid4()))
    await db_session.commit()
    assert await count_completions(db_session) == 1


async def test_deleting_a_learner_deletes_their_completions(
    db_session: AsyncSession, user_id: uuid.UUID
):
    db_session.add(StepCompletion(user_id=user_id, step_uuid=STEP))
    await db_session.commit()

    await db_session.execute(delete(User).where(User.id == user_id))
    await db_session.commit()

    assert await count_completions(db_session) == 0
