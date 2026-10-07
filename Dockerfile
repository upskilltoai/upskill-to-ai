# Base image pinned by digest, not just the `python:3.14-slim` tag: a tag moves,
# so two builds months apart could otherwise silently sit on different base
# layers. Update deliberately, by replacing the digest.
FROM python:3.14-slim@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151 AS build

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Pin the Tailwind release instead of downloading "latest" on every build, so
# the image's CSS is built by the same version as local `make css`. Keep in
# step with TAILWINDCSS_VERSION in the Makefile.
ENV TAILWINDCSS_VERSION=v4.3.3

# Download Tailwind, then check it against the checksum Tailwind published for
# that release *before it is ever run* — the program comes straight from
# GitHub, and this is what proves it's the genuine file. A mismatch fails the
# build. pytailwindcss picks the file by CPU type (`uname -m`), so the expected
# checksum is picked the same way. Done before the app is copied in, so this
# layer is cached and only re-downloads when the version changes.
# Bumping the version: replace both checksums with the `tailwindcss-linux-x64`
# and `tailwindcss-linux-arm64` lines from that release's sha256sums.txt.
RUN uv run python -c "import os, pytailwindcss; pytailwindcss.install(os.environ['TAILWINDCSS_VERSION'])" \
 && case "$(uname -m)" in \
      x86_64)  expected=dc61b3ac6b8c9ca874c0cc4c57b2409791a64c5540404ca5f5367360babc313a ;; \
      aarch64) expected=55fd0b241214eff3de1e8ee4f22796662f2d2e7a49bcfca7477cfd0bac398195 ;; \
      *) echo "No Tailwind checksum recorded for $(uname -m)" >&2; exit 1 ;; \
    esac \
 && binary="$(uv run python -c "import os; from pytailwindcss.utils import get_bin_path; print(get_bin_path(os.environ['TAILWINDCSS_VERSION']))")" \
 && echo "$expected  $binary" | sha256sum -c -

# `assets/` holds the CSS build *inputs* (input.css and the vendored daisyUI
# plugin files). They're needed here to generate output.css, and deliberately
# never copied into the runtime stage below — they'd be dead weight in the
# image and, since app/static/ is publicly mounted, publicly downloadable.
COPY app ./app
COPY assets ./assets
RUN uv run tailwindcss -i assets/css/input.css -o app/static/css/output.css --minify

# ---- Runtime stage: only what's needed to actually run ----
FROM python:3.14-slim@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151 AS runtime

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
