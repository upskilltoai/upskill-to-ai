#!/usr/bin/env bash
#
# Project commands. Run `./run.sh` on its own to see what is available.
#
# This does the same job as the Makefile — pick whichever you prefer.

set -euo pipefail                 # stop on error, on undefined variable, on any failure in a pipe
cd "$(dirname "$0")"              # always run from the repo root, wherever this was invoked from

usage() {
  cat <<'EOF'
Usage: ./run.sh <command>

  content   Build the curriculum artifact (uuids, then compile)
  content-dev   Build content/curriculum.dev.json (local only, not shipped)
  uuids     Add uuids to any new phase, topic, objective, or step
  compile   Validate content and write content/curriculum.json
  schemas   Regenerate content/schemas/*.json from content_model.py
  test      Run the app's test suite
  lint      Lint (including security rules)
  format    Auto-format the code, and apply safe lint fixes
  typecheck Check types
  audit     Scan dependencies for known vulnerabilities
  check     Run everything — content build, lint, types, tests. The pre-commit/CI command
  dev       Run the app locally, reloading on code changes
  css       Build the Tailwind CSS once
  css-watch Rebuild Tailwind CSS automatically as templates change
  docker-build  Build the Docker image
  docker-run    Run the app in Docker — visit http://localhost:8000
  docker-stop   Stop and remove the running Docker container
  docker-logs   Follow the running container's logs
  compose-up    Build and start app + Postgres together
  compose-down  Stop and remove app + Postgres (keeps the data volume)
  compose-logs  Follow every service's logs together
EOF
}

uuids() {
  uv run python scripts/inject_uuids.py
}

compile_curriculum() {
  uv run python scripts/compile_curriculum.py
}

generate_schemas() {
  uv run python scripts/generate_schemas.py
}

content() {
  uuids
  compile_curriculum
}

content_dev() {
  uuids
  uv run python scripts/compile_curriculum.py --dev-fixtures
}

run_tests() {
  uv run pytest
}

lint() {
  uv run ruff check .
}

format_code() {
  uv run ruff check . --fix
  uv run ruff format .
}

typecheck() {
  uv run pyright
}

audit() {
  uv run pip-audit
}

check() {
  content
  lint
  typecheck
  run_tests
}

dev() {
  uv run uvicorn app.main:app --reload --port 8000
}

css_build() {
  uv run tailwindcss -i assets/css/input.css -o app/static/css/output.css
}

css_watch() {
  uv run tailwindcss -i assets/css/input.css -o app/static/css/output.css --watch
}

docker_build() {
  docker build -t upskill-to-ai .
}

docker_run() {
  docker rm -f upskill-to-ai-app 2>/dev/null || true
  docker run -d --name upskill-to-ai-app -p 8000:8000 upskill-to-ai
}

docker_stop() {
  docker rm -f upskill-to-ai-app
}

docker_logs() {
  docker logs -f upskill-to-ai-app
}

compose_up() {
  docker compose up -d --build
}

compose_down() {
  docker compose down
}

compose_logs() {
  docker compose logs -f
}

case "${1:-}" in
  content)            content ;;
  content-dev)        content_dev ;;
  uuids)              uuids ;;
  compile)            compile_curriculum ;;
  schemas)            generate_schemas ;;
  test)               run_tests ;;
  lint)               lint ;;
  format)             format_code ;;
  typecheck)          typecheck ;;
  audit)              audit ;;
  check)              check ;;
  dev)                dev ;;
  css)                css_build ;;
  css-watch)          css_watch ;;
  docker-build)       docker_build ;;
  docker-run)         docker_run ;;
  docker-stop)        docker_stop ;;
  docker-logs)        docker_logs ;;
  compose-up)         compose_up ;;
  compose-down)       compose_down ;;
  compose-logs)       compose_logs ;;
  "" | help | -h | --help)  usage ;;
  *)
    echo "Unknown command: $1" >&2
    echo >&2
    usage >&2
    exit 1
    ;;
esac
