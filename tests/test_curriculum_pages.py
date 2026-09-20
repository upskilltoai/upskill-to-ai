from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_curriculum_index_lists_real_phases():
    response = client.get("/curriculum")
    assert response.status_code == 200
    assert "AI and LLM Foundations" in response.text
