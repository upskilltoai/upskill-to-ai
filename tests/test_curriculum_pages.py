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
