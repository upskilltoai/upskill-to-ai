"""Curriculum pages, rendered against a small test curriculum the tests own.

The tests swap in their own made-up curriculum instead of reading the real
`curriculum.json`, so changing real content (fixing a typo in a step title,
say) can never break an application test — curriculum edits are data PRs,
and contributors shouldn't have to touch Python. One smoke test still walks
the *real* curriculum, checking only that every page renders, never wording.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from content_model import Curriculum

client = TestClient(app)


def _id() -> str:
    return str(uuid.uuid4())


def _step(order: int, **fields) -> dict:
    return {"uuid": _id(), "order": order, "description": "A test step.", **fields}


TEST_CURRICULUM = Curriculum.model_validate(
    {
        "version": 1,
        "generated_at": "2026-01-01T00:00:00",
        "phases": [
            {
                "uuid": _id(),
                "slug": "phase1",
                "name": "Test Phase",
                "short_description": "A phase that exists only in the tests.",
                "description": "A phase that exists only in the tests.",
                "order": 1,
                "estimated_minutes": 30,
                "topics": [
                    {
                        "uuid": _id(),
                        "slug": "test-topic",
                        "name": "Test Topic",
                        "description": "A topic that exists only in the tests.",
                        "estimated_minutes": 20,
                        "objectives": [
                            {"uuid": _id(), "order": 1, "text": "Test objective text"}
                        ],
                        "steps": [
                            # One resource: the step title itself is the link.
                            _step(
                                1,
                                action="watch",
                                title="Watch the test video",
                                resources=[{"url": "https://example.com/video"}],
                            ),
                            # Several resources: plain title, each resource listed.
                            _step(
                                2,
                                action="read",
                                title="Read the test pages",
                                optional=True,
                                resources=[
                                    {
                                        "label": "Page one",
                                        "url": "https://example.com/one",
                                    },
                                    {
                                        "label": "Page two",
                                        "url": "https://example.com/two",
                                    },
                                ],
                            ),
                            # Variants: one tab per provider, each with its own text.
                            _step(
                                3,
                                action="practice",
                                title="Try the test provider",
                                optional=True,
                                variant_dimension="provider",
                                variants=[
                                    {
                                        "key": "alpha",
                                        "label": "Alpha",
                                        "description": "Alpha's own explanation of this step",
                                        "resources": [
                                            {
                                                "label": "Open the Alpha guide",
                                                "url": "https://example.com/alpha",
                                            }
                                        ],
                                    },
                                    {
                                        "key": "beta",
                                        "label": "Beta",
                                        "description": "Beta's own explanation of this step",
                                        "resources": [
                                            {
                                                "label": "Open the Beta guide",
                                                "url": "https://example.com/beta",
                                            }
                                        ],
                                    },
                                ],
                            ),
                        ],
                    },
                    {
                        "uuid": _id(),
                        "slug": "second-topic",
                        "name": "Second Test Topic",
                        "description": "Another test topic.",
                        "estimated_minutes": 10,
                        "is_capstone": True,
                        "objectives": [
                            {"uuid": _id(), "order": 1, "text": "Another objective"}
                        ],
                        "steps": [
                            _step(1, action="explore", title="Explore something")
                        ],
                    },
                ],
            }
        ],
    }
)


@pytest.fixture
def test_curriculum(monkeypatch: pytest.MonkeyPatch) -> Curriculum:
    """Swap the test curriculum in for one test; monkeypatch puts the real one back."""
    monkeypatch.setattr(app.state, "curriculum", TEST_CURRICULUM)
    return TEST_CURRICULUM


def test_curriculum_index_lists_phases(test_curriculum):
    response = client.get("/curriculum")
    assert response.status_code == 200
    assert "Test Phase" in response.text


def test_phase_page_lists_its_topics(test_curriculum):
    response = client.get("/curriculum/phase1")
    assert response.status_code == 200
    assert "Test Topic" in response.text
    assert "Second Test Topic" in response.text


def test_topic_page_lists_objectives_and_steps(test_curriculum):
    response = client.get("/curriculum/phase1/test-topic")
    assert response.status_code == 200
    assert "Test objective text" in response.text
    assert "Read the test pages" in response.text


def test_single_resource_step_title_is_the_link(test_curriculum):
    response = client.get("/curriculum/phase1/test-topic")
    assert "Watch" in response.text  # the action badge
    assert (
        '<a href="https://example.com/video" class="link link-hover font-semibold"'
        in response.text
    )
    assert "Watch the test video</a>" in response.text


def test_multi_resource_step_title_is_plain_text(test_curriculum):
    response = client.get("/curriculum/phase1/test-topic")
    # More than one resource: the title can't point at a single URL...
    assert "<strong>Read the test pages</strong>" in response.text
    # ...so each resource is listed separately instead.
    assert 'href="https://example.com/one"' in response.text
    assert 'href="https://example.com/two"' in response.text


def test_variant_tabs_show_their_own_description_and_phrased_link(test_curriculum):
    response = client.get("/curriculum/phase1/test-topic")
    assert "Alpha" in response.text
    assert "Beta" in response.text
    # Each variant explains its own resource rather than sharing the step's...
    assert "Alpha&#39;s own explanation of this step" in response.text
    assert "Beta&#39;s own explanation of this step" in response.text
    # ...and the link text is a full phrase, not a bare page title.
    assert "Open the Alpha guide" in response.text
    assert 'href="https://example.com/beta"' in response.text


def test_optional_steps_are_tagged_and_others_are_not(test_curriculum):
    response = client.get("/curriculum/phase1/test-topic")
    # Two of the three test steps are optional.
    assert response.text.count(">Optional</span>") == 2


def test_unknown_phase_and_topic_404(test_curriculum):
    assert client.get("/curriculum/phase99").status_code == 404
    assert client.get("/curriculum/phase1/no-such-topic").status_code == 404


def test_404s_render_the_styled_page_not_json(test_curriculum):
    for path in ("/curriculum/phase99", "/curriculum/phase1/nope", "/no-such-route"):
        response = client.get(path)
        assert response.status_code == 404, path
        assert "text/html" in response.headers["content-type"], path
        assert "Not found" in response.text, path
        # The internal detail message never reaches the page.
        assert "phase99" not in response.text, path


def test_every_real_phase_and_topic_page_renders():
    """Smoke test on the real curriculum: every page loads. Wording is never checked."""
    real = app.state.curriculum
    assert real is not TEST_CURRICULUM
    assert client.get("/curriculum").status_code == 200
    for phase in real.phases:
        assert client.get(f"/curriculum/{phase.slug}").status_code == 200, phase.slug
        for topic in phase.topics:
            path = f"/curriculum/{phase.slug}/{topic.slug}"
            assert client.get(path).status_code == 200, path
