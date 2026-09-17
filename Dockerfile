# ---- Build stage: install everything (including dev), generate CSS ----
FROM python:3.12-slim AS build

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY app ./app
RUN uv run tailwindcss -i app/static/css/input.css -o app/static/css/output.css --minify

# ---- Runtime stage: only what's needed to actually run ----
FROM python:3.12-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app
COPY --from=build /app/app/static/css/output.css ./app/static/css/output.css

ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
