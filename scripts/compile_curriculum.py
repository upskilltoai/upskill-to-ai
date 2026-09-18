"""Validate authored YAML and compile it into a single versioned artifact.

The application never reads YAML. It reads `content/curriculum.json`, produced
here, so that a malformed edit fails at build time rather than in front of a
learner.

    uv run python scripts/compile_curriculum.py

Structural checks beyond JSON Schema:

* every topic slug listed by a phase has a matching file, and vice versa
* the last topic of every phase is marked `is_capstone`
* a step does not mix shared `resources` with `variants`
* every uuid in the curriculum is unique
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
SCHEMAS = CONTENT / "schemas"
OUTPUT = CONTENT / "curriculum.json"

# Named zone rather than a fixed offset: EST and EDT are the same zone at
# different times of year, so "-05:00" would be wrong from March to November.
# Naming the zone explicitly (rather than using the machine's local time) also
# means a build produces the same wall-clock reading wherever it runs — a CI
# runner set to UTC included.
BUILD_TIMEZONE = ZoneInfo("America/New_York")


class ContentError(Exception):
    """A problem an author needs to fix."""


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def make_validator(name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate(validator: Draft202012Validator, data, path: Path) -> None:
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if not errors:
        return
    lines = [f"{path.relative_to(ROOT)} failed validation:"]
    for error in errors:
        location = " → ".join(str(part) for part in error.path) or "(root)"
        lines.append(f"  at {location}: {error.message}")
    raise ContentError("\n".join(lines))


def check_steps(topic: dict, path: Path) -> None:
    for step in topic["steps"]:
        has_resources = bool(step.get("resources"))
        has_variants = bool(step.get("variants"))
        if has_resources and has_variants:
            raise ContentError(
                f"{path.relative_to(ROOT)}: step {step['order']} "
                f"({step['title']!r}) declares both `resources` and `variants`. "
                "Use `resources` for links everyone sees, `variants` for a "
                "learner choice — not both."
            )


def collect_uuids(node, seen: dict[str, str], where: str) -> None:
    if isinstance(node, dict):
        if "uuid" in node:
            label = node.get("title") or node.get("name") or node.get("text", "")
            key = node["uuid"]
            if key in seen:
                raise ContentError(
                    f"Duplicate uuid {key}\n  first:  {seen[key]}\n  second: {where} — {label}"
                )
            seen[key] = f"{where} — {label}"
        for value in node.values():
            collect_uuids(value, seen, where)
    elif isinstance(node, list):
        for item in node:
            collect_uuids(item, seen, where)


def build_phase(phase_dir: Path, topic_validator: Draft202012Validator) -> dict:
    phase_path = phase_dir / "_phase.yaml"
    if not phase_path.exists():
        raise ContentError(f"{phase_dir.relative_to(ROOT)} has no _phase.yaml")

    phase = load_yaml(phase_path)
    validate(make_validator("phase.schema.json"), phase, phase_path)

    listed = list(phase["topics"])
    on_disk = {p.stem for p in phase_dir.glob("*.yaml") if p.name != "_phase.yaml"}

    missing = [slug for slug in listed if slug not in on_disk]
    if missing:
        raise ContentError(
            f"{phase_path.relative_to(ROOT)} lists topics with no file: {', '.join(missing)}"
        )

    orphans = sorted(on_disk - set(listed))
    if orphans:
        raise ContentError(
            f"{phase_dir.relative_to(ROOT)} contains topic files not listed in "
            f"_phase.yaml: {', '.join(orphans)}. Order lives in the phase file, "
            "so an unlisted topic would never be shown."
        )

    topics = []
    for slug in listed:
        path = phase_dir / f"{slug}.yaml"
        topic = load_yaml(path)
        validate(topic_validator, topic, path)
        if topic["slug"] != slug:
            raise ContentError(
                f"{path.relative_to(ROOT)}: slug is {topic['slug']!r} but the "
                f"filename says {slug!r}"
            )
        check_steps(topic, path)
        topics.append(topic)

    if not topics[-1].get("is_capstone"):
        raise ContentError(
            f"{phase_path.relative_to(ROOT)}: the last topic ({topics[-1]['slug']}) "
            "must set `is_capstone: true` — every phase ends in a capstone."
        )
    for topic in topics[:-1]:
        if topic.get("is_capstone"):
            raise ContentError(
                f"{phase_dir.relative_to(ROOT)}/{topic['slug']}.yaml is marked "
                "`is_capstone` but is not the final topic of the phase."
            )

    phase["topics"] = topics
    phase["estimated_minutes"] = sum(t["estimated_minutes"] for t in topics)
    return phase


def main() -> int:
    try:
        meta = load_yaml(CONTENT / "curriculum.meta.yaml")
        version = meta["curriculum_version"]

        topic_validator = make_validator("topic.schema.json")
        phase_dirs = sorted((CONTENT / "phases").glob("phase*"))
        if not phase_dirs:
            raise ContentError("No phases found under content/phases")

        phases = [build_phase(d, topic_validator) for d in phase_dirs]
        phases.sort(key=lambda p: p["order"])

        seen: dict[str, str] = {}
        for phase in phases:
            collect_uuids(phase, seen, phase["slug"])

        artifact = {
            "version": version,
            "generated_at": datetime.now(BUILD_TIMEZONE).isoformat(timespec="seconds"),
            "phases": phases,
        }
        OUTPUT.write_text(
            json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    except ContentError as error:
        print(f"\n✗ {error}\n", file=sys.stderr)
        return 1

    steps = sum(len(t["steps"]) for p in phases for t in p["topics"])
    objectives = sum(len(t["objectives"]) for p in phases for t in p["topics"])
    topics = sum(len(p["topics"]) for p in phases)
    hours = sum(p["estimated_minutes"] for p in phases) / 60

    print(f"✓ curriculum.json v{version}")
    print(
        f"  {len(phases)} phase(s), {topics} topic(s), {objectives} objective(s), {steps} step(s)"
    )
    print(f"  {len(seen)} unique uuid(s), ~{hours:.0f}h of core content")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
