"""Routes for browsing the curriculum. A vertical slice: this feature's
routes live here, not in `app/main.py` — see `app/curriculum/service.py`
for the lookups they call, and `app/curriculum/loader.py` for how
`request.app.state.curriculum` got there in the first place.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.curriculum.service import get_phase
from app.templates import templates

router = APIRouter()


@router.get("/curriculum")
def curriculum_index(request: Request):
    curriculum = request.app.state.curriculum
    return templates.TemplateResponse(
        request, "curriculum_index.html", {"phases": curriculum.phases}
    )


@router.get("/curriculum/{phase_slug}")
def phase_page(request: Request, phase_slug: str):
    curriculum = request.app.state.curriculum
    phase = get_phase(curriculum, phase_slug)
    if phase is None:
        raise HTTPException(status_code=404, detail=f"No phase '{phase_slug}'")
    return templates.TemplateResponse(request, "phase.html", {"phase": phase})
