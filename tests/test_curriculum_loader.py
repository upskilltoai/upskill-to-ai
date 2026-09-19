import json
from pathlib import Path

import pytest

from app.curriculum.loader import CURRICULUM_JSON, load_curriculum
from content_model import Curriculum


def test_loads_the_real_curriculum_json():
    curriculum = load_curriculum()
    assert isinstance(curriculum, Curriculum)
    assert len(curriculum.phases) >= 1


def test_missing_file_raises_runtime_error(tmp_path: Path):
    missing = tmp_path / "curriculum.json"
    with pytest.raises(RuntimeError, match="does not exist"):
        load_curriculum(path=missing)


def test_malformed_content_raises_runtime_error(tmp_path: Path):
    real = json.loads(CURRICULUM_JSON.read_text(encoding="utf-8"))
    real["phases"] = []  # violates `min_length=1` on `Curriculum.phases`

    broken = tmp_path / "curriculum.json"
    broken.write_text(json.dumps(real), encoding="utf-8")

    with pytest.raises(RuntimeError, match="does not match the expected shape"):
        load_curriculum(path=broken)
