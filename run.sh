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
  uuids     Add uuids to any new phase, topic, objective, or step
  compile   Validate content and write content/curriculum.json
  test      Run the app's test suite
  check     Run everything — content build + tests. The pre-commit/CI command
  dev       Run the app locally, reloading on code changes
EOF
}

uuids() {
  uv run python scripts/inject_uuids.py
}

compile_curriculum() {
  uv run python scripts/compile_curriculum.py
}

content() {
  uuids
  compile_curriculum
}

run_tests() {
  uv run pytest
}

check() {
  content
  run_tests
}

dev() {
  uv run uvicorn app.main:app --reload --port 8000
}

case "${1:-}" in
  content)            content ;;
  uuids)              uuids ;;
  compile)            compile_curriculum ;;
  test)               run_tests ;;
  check)              check ;;
  dev)                dev ;;
  "" | help | -h | --help)  usage ;;
  *)
    echo "Unknown command: $1" >&2
    echo >&2
    usage >&2
    exit 1
    ;;
esac
