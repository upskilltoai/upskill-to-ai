# Project commands. Run `make` on its own to see what is available.
#
# Note for editing: recipe lines (the indented ones) must start with a real
# TAB character, not spaces. Make is strict about this and the error message
# it gives is unhelpful.

.DEFAULT_GOAL := help
.PHONY: help content uuids compile test check dev css css-watch docker-build docker-run docker-stop docker-logs

help:  ## Show available commands
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

content: uuids compile  ## Build the curriculum artifact (uuids, then compile)

uuids:  ## Add uuids to any new phase, topic, objective, or step
	@uv run python scripts/inject_uuids.py

compile:  ## Validate content and write content/curriculum.json
	@uv run python scripts/compile_curriculum.py

test:  ## Run the app's test suite
	@uv run pytest

check: content test  ## Run everything — content build + tests. The pre-commit/CI command

dev:  ## Run the app locally, reloading on code changes — visit http://localhost:8000
	@uv run uvicorn app.main:app --reload --port 8000

css:  ## Build the Tailwind CSS once
	@uv run tailwindcss -i app/static/css/input.css -o app/static/css/output.css

css-watch:  ## Rebuild Tailwind CSS automatically as templates change — run alongside `make dev`
	@uv run tailwindcss -i app/static/css/input.css -o app/static/css/output.css --watch

docker-build:  ## Build the Docker image
	@docker build -t upskill-to-ai .

docker-run:  ## Run the app in Docker — visit http://localhost:8000
	@docker rm -f upskill-to-ai-app 2>/dev/null || true
	@docker run -d --name upskill-to-ai-app -p 8000:8000 upskill-to-ai

docker-stop:  ## Stop and remove the running Docker container
	@docker rm -f upskill-to-ai-app

docker-logs:  ## Follow the running container's logs
	@docker logs -f upskill-to-ai-app
