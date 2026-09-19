"""Generate content/schemas/*.json from the Pydantic models in content_model.py.

The models are the source of truth now; these files are build output, same
relationship curriculum.json has to the authored YAML. Never hand-edit them —
the next run of this script overwrites whatever's here.

    uv run python scripts/generate_schemas.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "content" / "schemas"

# content_model.py lives at the repo root, not inside scripts/ — running this
# file directly (`python scripts/generate_schemas.py`) only puts scripts/
# itself on the import path, not ROOT, so the plain import would fail.
sys.path.insert(0, str(ROOT))

from content_model import Phase, Topic  # noqa: E402


def build_schema(model: type, *, schema_id: str, title: str, description: str) -> dict:
    schema = model.model_json_schema()
    # Prepend the metadata a hand-written schema would open with, so the
    # files stay self-describing and diff cleanly against their old versions.
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": schema_id,
        "title": title,
        "description": description,
        **schema,
    }


def main() -> int:
    phase_schema = build_schema(
        Phase,
        schema_id="https://upskill-to-ai/schemas/phase.schema.json",
        title="Phase",
        description="A competency cluster. The last topic of every phase is a capstone.",
    )
    topic_schema = build_schema(
        Topic,
        schema_id="https://upskill-to-ai/schemas/topic.schema.json",
        title="Topic",
        description="A group of related steps within a phase.",
    )

    (SCHEMAS / "phase.schema.json").write_text(
        json.dumps(phase_schema, indent=2) + "\n", encoding="utf-8"
    )
    (SCHEMAS / "topic.schema.json").write_text(
        json.dumps(topic_schema, indent=2) + "\n", encoding="utf-8"
    )

    print("✓ content/schemas/phase.schema.json")
    print("✓ content/schemas/topic.schema.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
