from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.curriculum.loader import load_curriculum
from app.logging import configure_logging
from app.middleware import SecurityHeadersMiddleware

configure_logging()

curriculum = load_curriculum()

_is_dev = settings.environment == "development"

# FastAPI's interactive docs are on by default. They're useful locally, but
# outside development they publish a machine-readable map of every endpoint to
# anyone who asks — so they're switched off there.
app = FastAPI(
    docs_url="/docs" if _is_dev else None,
    redoc_url="/redoc" if _is_dev else None,
    openapi_url="/openapi.json" if _is_dev else None,
)

app.add_middleware(SecurityHeadersMiddleware)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "home.html")
