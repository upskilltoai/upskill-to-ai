"""Loads and validates the compiled curriculum artifact at startup.

Deliberately not a FastAPI `lifespan` hook — `lifespan` earns its keep for
resources that need shutdown cleanup (a database pool). A static JSON file
has none, so a plain module-level call in `app/main.py` is enough, and it
also means the load happens (and can fail) at import time, before the app
even starts accepting requests.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from content_model import Curriculum

CURRICULUM_JSON = (
    Path(__file__).resolve().parent.parent.parent / "content" / "curriculum.json"
)


def load_curriculum(path: Path = CURRICULUM_JSON) -> Curriculum:
    """Read and validate the compiled curriculum artifact.

    Raises `RuntimeError` on a missing or malformed file rather than letting
    a raw `FileNotFoundError`/`ValidationError` propagate unexplained — the
    fix (`make content`, or "read the error and edit the offending YAML") is
    what a maintainer sees first, not a Pydantic stack trace.
    """
    if not path.exists():
        raise RuntimeError(f"{path} does not exist. Run `make content` to build it.")

    data = json.loads(path.read_text(encoding="utf-8"))

    try:
        return Curriculum.model_validate(data)
    except ValidationError as error:
        raise RuntimeError(
            f"{path} does not match the expected shape:\n{error}"
        ) from error
