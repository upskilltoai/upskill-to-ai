"""The compiler's artifact writing: `generated_at` moves only when content does."""

import json
from pathlib import Path

from scripts.compile_curriculum import write_artifact

PHASES = [{"slug": "phase1", "name": "Foundations"}]
LONG_AGO = "2020-01-01T00:00:00-05:00"


def backdate(output: Path) -> None:
    """Pretend the file was built long ago, so a rewrite would be visible."""
    data = json.loads(output.read_text(encoding="utf-8"))
    output.write_text(
        output.read_text(encoding="utf-8").replace(data["generated_at"], LONG_AGO),
        encoding="utf-8",
    )


def generated_at(output: Path) -> str:
    return json.loads(output.read_text(encoding="utf-8"))["generated_at"]


def test_first_build_writes_the_file(tmp_path: Path):
    output = tmp_path / "curriculum.json"
    assert write_artifact(output, 1, PHASES) is True
    assert json.loads(output.read_text(encoding="utf-8"))["phases"] == PHASES


def test_rebuilding_unchanged_content_leaves_the_file_alone(tmp_path: Path):
    output = tmp_path / "curriculum.json"
    write_artifact(output, 1, PHASES)
    backdate(output)
    before = output.read_bytes()

    assert write_artifact(output, 1, PHASES) is False
    assert output.read_bytes() == before
    assert generated_at(output) == LONG_AGO


def test_changed_content_gets_a_fresh_timestamp(tmp_path: Path):
    output = tmp_path / "curriculum.json"
    write_artifact(output, 1, PHASES)
    backdate(output)

    changed = [{"slug": "phase1", "name": "Foundations, revised"}]
    assert write_artifact(output, 1, changed) is True
    assert generated_at(output) != LONG_AGO
    assert json.loads(output.read_text(encoding="utf-8"))["phases"] == changed


def test_a_version_bump_alone_counts_as_a_change(tmp_path: Path):
    output = tmp_path / "curriculum.json"
    write_artifact(output, 1, PHASES)
    backdate(output)

    assert write_artifact(output, 2, PHASES) is True
    assert generated_at(output) != LONG_AGO


def test_an_unreadable_existing_file_is_simply_rewritten(tmp_path: Path):
    output = tmp_path / "curriculum.json"
    output.write_text("not json", encoding="utf-8")

    assert write_artifact(output, 1, PHASES) is True
    assert json.loads(output.read_text(encoding="utf-8"))["version"] == 1
