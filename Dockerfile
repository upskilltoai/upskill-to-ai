# Base image pinned by digest, not just the `python:3.12-slim` tag: a tag moves,
# so two builds months apart could otherwise silently sit on different base
# layers. Update deliberately, by replacing the digest.
FROM python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea AS build

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# `assets/` holds the CSS build *inputs* (input.css and the vendored daisyUI
# plugin files). They're needed here to generate output.css, and deliberately
# never copied into the runtime stage below — they'd be dead weight in the
# image and, since app/static/ is publicly mounted, publicly downloadable.
COPY app ./app
COPY assets ./assets
RUN uv run tailwindcss -i assets/css/input.css -o app/static/css/output.css --minify

# ---- Runtime stage: only what's needed to actually run ----
FROM python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea AS runtime

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
# Compile dependencies to bytecode now, at build time. The app user can't
# write under /app (see the end of this file), so Python couldn't cache
# compiled files at runtime — without this, every container start would
# recompile all of FastAPI, Pydantic and SQLAlchemy in memory.
ENV UV_COMPILE_BYTECODE=1
RUN uv sync --frozen --no-dev

COPY app ./app

# `content_model.py` sits at the repo root, not inside app/, because the
# content pipeline scripts share it. That makes it easy to forget that the
# app imports it too — `app/curriculum/` parses curriculum.json through
# these models, so without this the image starts and immediately dies on
# ModuleNotFoundError.
COPY content_model.py ./content_model.py

# Only the compiled artifact, never content/ as a whole. The app never reads
# YAML (that's the whole point of compiling), so the sources would be dead
# weight — and content/ also holds dev-fixtures/ and curriculum.dev.json,
# placeholder content that must never reach a real deployment.
COPY content/curriculum.json ./content/curriculum.json

# Migrations ship with the image so a deployment can run
# `alembic upgrade head` as a one-off job using this exact image, rather than
# needing a separate checkout with matching dependencies. The web process
# never runs them — see the Stage C rule that migrations are always an
# explicit command, never automatic at startup.
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations

COPY --from=build /app/app/static/css/output.css ./app/static/css/output.css

# Run as an unprivileged user. Containers default to root, which means any
# code-execution bug in the app would run as root inside the container —
# a much larger blast radius for no benefit, since nothing here needs root.
# Everything under /app stays owned by root, so appuser can read and run the
# code but not change it: a code-execution bug can't rewrite the app, its
# dependencies, or the migrations shipped alongside it. Nothing the app does
# at runtime writes to disk — logs go to stdout.
RUN useradd --create-home --uid 1000 appuser
USER appuser

ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
