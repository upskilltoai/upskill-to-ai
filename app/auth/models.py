"""The `User` table — one row per learner who has signed in with GitHub."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    # "users", not "user": `user` is a reserved word in Postgres, so a table
    # by that name has to be double-quoted in every raw query forever.
    __tablename__ = "users"

    # Our own ID, not GitHub's. Keeps the rest of the schema independent of
    # which sign-in provider created the account, and a random UUID can't be
    # enumerated the way /users/1, /users/2 can if it ever appears in a URL.
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # The stable identity from GitHub — this, not `login`, is how a returning
    # learner is recognised. BigInteger because GitHub's IDs are already in
    # the hundreds of millions and only grow.
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True)

    # Deliberately NOT unique. A GitHub user can rename themselves, and the
    # freed username can later be claimed by someone else — so two different
    # rows can legitimately have held the same login at different times.
    # Refreshed from GitHub on every sign-in.
    login: Mapped[str] = mapped_column(String(39))  # GitHub's own maximum

    avatar_url: Mapped[str] = mapped_column(String(500))

    # Timezone-aware (`timestamptz`): stores an absolute moment, so the value
    # can't be misread when the server and the viewer are in different zones.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # `onupdate` is applied by SQLAlchemy when a row is changed through the
    # ORM — a raw UPDATE run by hand won't touch it.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
