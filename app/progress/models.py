"""The `StepCompletion` table — one row per step a learner has ticked off."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class StepCompletion(Base):
    __tablename__ = "step_completions"

    # The primary key is the pair (user_id, step_uuid): a learner either has
    # completed a step or hasn't, so the pair *is* the row's identity and can
    # never appear twice. Un-ticking a step deletes the row. Because user_id
    # comes first, the same index also answers "every step this learner has
    # completed" — the query the progress pages run most — with no extra index.
    #
    # ON DELETE CASCADE: deleting a user deletes their completions with them,
    # rather than leaving rows that point at nobody.
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )

    # Deliberately NOT a foreign key. Steps live in content/curriculum.json,
    # not in the database, so Postgres has nothing to check this against. What
    # keeps it valid instead is the content rule that a step's uuid never
    # changes once published (content/README.md) — change one and every
    # completion of that step silently stops matching anything.
    step_uuid: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
