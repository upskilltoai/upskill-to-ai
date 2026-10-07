# Project commands. Run `make` on its own to see what is available.
#
# Every command has a `## description` on its target line, and `##@ Name`
# lines start a group — `make help` builds its listing from those, so a new
# command shows up in the help automatically. Add it under the right group.
#
# Note for editing: recipe lines (the indented ones) must start with a real
# TAB character, not spaces. Make is strict about this and the error message
# it gives is unhelpful.

.DEFAULT_GOAL := help
.PHONY: help dev css css-watch content content-dev uuids compile schemas \
	db db-shell migrate migration migrate-status \
	check test lint format typecheck audit \
	docker-build compose-up compose-down compose-logs

CSS_IN  := assets/css/input.css
CSS_OUT := app/static/css/output.css
IMAGE   := upskill-to-ai

# Which Tailwind release `pytailwindcss` downloads and runs. Unset, it fetches
# whatever is "latest" — once per machine, then reuses it forever — so a laptop
# and a fresh Docker build could quietly compile the CSS with different
# versions. `export` hands it to every command below. Keep in step with the
# same pin in the Dockerfile; bump both together, deliberately.
export TAILWINDCSS_VERSION := v4.3.3

help:  ## Show available commands
	@awk 'BEGIN {FS = ":.*## "} \
		/^##@/ {printf "\n\033[1m%s\033[0m\n", substr($$0, 5)} \
		/^[a-z-]+:.*## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

##@ Run

dev:  ## Run the app locally, reloading on code changes — visit http://localhost:8000
	@uv run uvicorn app.main:app --reload --port 8000

css:  ## Build the Tailwind CSS once
	@uv run tailwindcss -i $(CSS_IN) -o $(CSS_OUT)

css-watch:  ## Rebuild the CSS as templates change — run alongside `make dev`
	@uv run tailwindcss -i $(CSS_IN) -o $(CSS_OUT) --watch

##@ Content

content: uuids compile  ## Build the curriculum artifact (uuids, then compile)

content-dev: uuids  ## Build content/curriculum.dev.json with placeholder phases (local only, not shipped)
	@uv run python scripts/compile_curriculum.py --dev-fixtures

uuids:  ## Add uuids to any new phase, topic, objective, or step
	@uv run python scripts/inject_uuids.py

compile:  ## Validate content and write content/curriculum.json
	@uv run python scripts/compile_curriculum.py

schemas:  ## Regenerate content/schemas/*.json — run after editing content_model.py
	@uv run python scripts/generate_schemas.py

##@ Database

db:  ## Start the local Postgres (needed by migrations and the database tests)
	@docker compose up -d db

db-shell:  ## Open psql on the local development database
	@docker compose exec db psql -U upskill -d upskill

migrate:  ## Apply every pending migration
	@uv run alembic upgrade head

migration:  ## Create a migration from model changes — make migration m="add user table"
	@test -n "$(m)" || (echo 'Usage: make migration m="what changed"' && exit 1)
	@uv run alembic revision --autogenerate -m "$(m)"

migrate-status:  ## Show which migration the database is currently on
	@uv run alembic current

##@ Quality

check: content lint typecheck test  ## Run everything before committing — content build, lint, format check, types, tests

test:  ## Run the test suite (database tests are skipped unless `make db` is running)
	@uv run pytest

lint:  ## Lint (including security rules) and check formatting
	@uv run ruff check .
	@uv run ruff format --check .

format:  ## Auto-format the code, and apply safe lint fixes
	@uv run ruff check . --fix
	@uv run ruff format .

typecheck:  ## Check types
	@uv run pyright

audit:  ## Scan dependencies for known vulnerabilities
	@uv run pip-audit

##@ Docker

docker-build:  ## Build the production image on its own, to check it builds
	@docker build -t $(IMAGE) .

compose-up:  ## Build and start app + Postgres together — visit http://localhost:8000
	@docker compose up -d --build

compose-down:  ## Stop and remove app + Postgres (keeps the Postgres data volume)
	@docker compose down

compose-logs:  ## Follow every service's logs together
	@docker compose logs -f
