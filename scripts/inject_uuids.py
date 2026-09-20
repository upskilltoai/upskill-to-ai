"""Add a stable uuid to every phase, topic, objective, and step that lacks one.

Content is authored without uuids — writing them by hand is tedious and
error-prone. This script fills them in, in place, and never touches an existing
one: uuids are the identity progress records point at, so regenerating one would
orphan every learner's completion of that step.

Run it after authoring or adding content, before compiling.

    uv run python scripts/inject_uuids.py
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

from ruamel.yaml import YAML

CONTENT = Path(__file__).resolve().parent.parent / "content"

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096  # don't re-wrap folded scalars


def ensure_uuid(node, *, position: int = 0) -> bool:
    """Insert a uuid at `position` if absent. Returns True if one was added."""
    if "uuid" in node:
        return False
    node.insert(position, "uuid", str(uuid.uuid4()))
    return True


def process_file(path: Path) -> int:
    data = yaml.load(path)
    if data is None:
        return 0

    added = 0

    # The document itself is a phase or a topic.
    if ensure_uuid(data):
        added += 1

    for collection in ("objectives", "steps"):
        for item in data.get(collection) or []:
            if ensure_uuid(item):
                added += 1

    if added:
        yaml.dump(data, path)
    return added


def main() -> int:
    # Both roots: the real pipeline (`phases/`) and the dev-only placeholder
    # fixtures (`dev-fixtures/phases/`, see content/README.md) — a new
    # placeholder phase needs uuids injected too, same as real content.
    files = sorted(CONTENT.glob("phases/*/*.yaml")) + sorted(
        CONTENT.glob("dev-fixtures/phases/*/*.yaml")
    )
    if not files:
        print(f"No content found under {CONTENT}/phases", file=sys.stderr)
        return 1

    total = 0
    for path in files:
        added = process_file(path)
        total += added
        if added:
            print(f"  {path.relative_to(CONTENT)}: +{added}")

    print(f"\n{total} uuid(s) added across {len(files)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
