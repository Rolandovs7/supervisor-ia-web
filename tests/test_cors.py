from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

PREFLIGHT = {
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type,authorization",
}


def test_preflight_localhost():
    response = client.options(
        "/login",
        headers={**PREFLIGHT, "Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_preflight_127_0_0_1():
    response = client.options(
        "/upload",
        headers={**PREFLIGHT, "Origin": "http://127.0.0.1:5173"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_preflight_unknown_origin_is_not_allowed():
    response = client.options(
        "/login",
        headers={**PREFLIGHT, "Origin": "https://evil.example"},
    )
    assert "access-control-allow-origin" not in response.headers
