from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_security_headers_present_on_every_response():
    response = client.get("/")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "default-src 'self'" in response.headers["content-security-policy"]


def test_security_headers_apply_to_json_routes_too():
    # Not just HTML pages — middleware runs for every response.
    response = client.get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"


def test_csp_skipped_on_docs_so_swagger_ui_can_load():
    # Swagger UI pulls its CSS/JS from a public CDN, which `default-src 'self'`
    # blocks — the page would render blank. These routes are development-only,
    # so exempting them costs nothing in production, where they don't exist.
    response = client.get("/docs")
    assert response.status_code == 200
    assert "content-security-policy" not in response.headers
    # The other headers still apply.
    assert response.headers["x-content-type-options"] == "nosniff"


def test_hsts_absent_in_development():
    # HSTS on localhost would force https:// and break local development,
    # so it is deliberately only sent outside development.
    response = client.get("/")
    assert "strict-transport-security" not in response.headers
