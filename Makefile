# Project commands. Run `make` on its own to see what is available.
#
# Note for editing: recipe lines (the indented ones) must start with a real
# TAB character, not spaces. Make is strict about this and the error message
# it gives is unhelpful.

.DEFAULT_GOAL := help
.PHONY: help content uuids compile

help:  ## Show available commands
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

content: uuids compile  ## Build the curriculum artifact (uuids, then compile)

uuids:  ## Add uuids to any new phase, topic, objective, or step
	@uv run python scripts/inject_uuids.py

compile:  ## Validate content and write content/curriculum.json
	@uv run python scripts/compile_curriculum.py
