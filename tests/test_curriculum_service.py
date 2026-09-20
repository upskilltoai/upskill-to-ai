import uuid

from app.curriculum.service import get_phase, get_topic
from content_model import CompiledPhase, Curriculum, Objective, Step, Topic


def _topic(slug: str) -> Topic:
    return Topic(
        uuid=uuid.uuid4(),
        slug=slug,
        name=slug,
        description="d",
        estimated_minutes=1,
        objectives=[Objective(uuid=uuid.uuid4(), order=1, text="o")],
        steps=[
            Step(
                uuid=uuid.uuid4(),
                order=1,
                action="read",
                title="t",
                description="d",
            )
        ],
    )


def _curriculum() -> Curriculum:
    phase = CompiledPhase(
        uuid=uuid.uuid4(),
        slug="phase1",
        name="Phase One",
        short_description="d",
        description="d",
        order=1,
        topics=[_topic("first-topic")],
        estimated_minutes=1,
    )
    return Curriculum(version=1, generated_at="2026-01-01T00:00:00", phases=[phase])


def test_get_phase_found():
    phase = get_phase(_curriculum(), "phase1")
    assert phase is not None
    assert phase.name == "Phase One"


def test_get_phase_not_found():
    assert get_phase(_curriculum(), "phase99") is None


def test_get_topic_found():
    topic = get_topic(_curriculum(), "phase1", "first-topic")
    assert topic is not None
    assert topic.name == "first-topic"


def test_get_topic_not_found_in_existing_phase():
    assert get_topic(_curriculum(), "phase1", "no-such-topic") is None


def test_get_topic_not_found_when_phase_missing():
    assert get_topic(_curriculum(), "phase99", "first-topic") is None
