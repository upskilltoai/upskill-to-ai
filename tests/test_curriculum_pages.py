from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_curriculum_index_lists_real_phases():
    response = client.get("/curriculum")
    assert response.status_code == 200
    assert "AI and LLM Foundations" in response.text


def test_phase_page_lists_its_topics():
    response = client.get("/curriculum/phase1")
    assert response.status_code == 200
    assert "How LLMs Work" in response.text


def test_phase_page_404s_for_unknown_slug():
    response = client.get("/curriculum/phase99")
    assert response.status_code == 404


def test_topic_page_lists_objectives_and_steps():
    response = client.get("/curriculum/phase1/how-llms-work")
    assert response.status_code == 200
    assert "next-token prediction" in response.text
    assert "What Is a Large Language Model?" in response.text


def test_topic_page_renders_step_action_badge_and_title_link():
    response = client.get("/curriculum/phase1/how-llms-work")
    assert response.status_code == 200
    assert "Watch" in response.text
    # A single-resource step's title itself is the resource link.
    assert (
        '<a href="https://www.youtube.com/watch?v=LPZh9BOjkQs" class="link link-hover font-semibold"'
        in response.text
    )
    assert "What Is a Large Language Model?</a>" in response.text


def test_topic_page_renders_multi_resource_step_titles_as_plain_text():
    response = client.get("/curriculum/phase1/model-landscape")
    assert response.status_code == 200
    # More than one resource: title can't point at a single URL, so it stays plain...
    assert "<strong>Frontier Model Providers</strong>" in response.text
    # ...and each resource is listed separately instead.
    assert 'href="https://platform.claude.com/docs/en/models/overview"' in response.text
    assert 'href="https://platform.openai.com/docs/models"' in response.text


def test_topic_page_renders_variant_steps():
    response = client.get("/curriculum/phase1/first-api-call")
    assert response.status_code == 200
    assert "Anthropic" in response.text
    assert "OpenAI" in response.text
    assert 'href="https://platform.claude.com/docs/en/get-started"' in response.text
    assert 'href="https://platform.openai.com/docs/guides/text"' in response.text


def test_topic_page_404s_for_unknown_topic():
    response = client.get("/curriculum/phase1/no-such-topic")
    assert response.status_code == 404
