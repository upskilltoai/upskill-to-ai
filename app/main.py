from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.curriculum.loader import load_curriculum
from app.curriculum.router import router as curriculum_router
from app.logging import configure_logging
from app.middleware import SecurityHeadersMiddleware
from app.templates import templates

configure_logging()

_is_dev = settings.environment == "development"

# FastAPI's interactive docs are on by default. They're useful locally, but
# outside development they publish a machine-readable map of every endpoint to
# anyone who asks — so they're switched off there.
app = FastAPI(
    docs_url="/docs" if _is_dev else None,
    redoc_url="/redoc" if _is_dev else None,
    openapi_url="/openapi.json" if _is_dev else None,
)

# On `app.state`, not a bare module-level variable: route handlers reach it
# via `request.app.state.curriculum` (see `app/curriculum/router.py`)
# without importing this module and risking a circular import. Still runs
# at plain import time, before uvicorn ever starts accepting requests, so a
# missing/malformed curriculum.json still fails loudly at startup.
app.state.curriculum = (
    load_curriculum(Path(settings.curriculum_json_path))
    if settings.curriculum_json_path
    else load_curriculum()
)

app.add_middleware(SecurityHeadersMiddleware)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(curriculum_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "home.html")
