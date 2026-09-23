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


def test_topic_page_404s_for_unknown_topic():
    response = client.get("/curriculum/phase1/no-such-topic")
    assert response.status_code == 404
