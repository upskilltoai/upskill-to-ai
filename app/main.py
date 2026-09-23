from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

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


# Registered by status code rather than by exception class, so this covers
# both kinds of 404 with one handler: the ones the curriculum routes raise
# for an unknown slug, and the one Starlette raises for a URL that matches
# no route at all. Lives here rather than in a feature folder because any
# feature's routes can 404.
#
# `exc.detail` is deliberately not shown. It exists for logs, and echoing it
# would reflect whatever slug the visitor typed back onto the page — Jinja
# escapes it, so it isn't an injection risk, but a learner following a stale
# link is better served by one clear sentence than by the internal message.
@app.exception_handler(404)
def not_found(request: Request, exc: StarletteHTTPException) -> Response:
    return templates.TemplateResponse(request, "404.html", status_code=404)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "home.html")
