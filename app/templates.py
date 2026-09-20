"""The one shared Jinja2Templates instance, used by every feature's routes.

Cross-cutting, so it lives directly under `app/` rather than inside any one
feature folder (`app/curriculum/`, etc.) — the same rule `app/config.py`
and `app/logging.py` already follow.
"""

from __future__ import annotations

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")
