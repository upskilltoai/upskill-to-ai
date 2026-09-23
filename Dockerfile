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

COPY --from=build /app/app/static/css/output.css ./app/static/css/output.css

# Run as an unprivileged user. Containers default to root, which means any
# code-execution bug in the app would run as root inside the container —
# a much larger blast radius for no benefit, since nothing here needs root.
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
