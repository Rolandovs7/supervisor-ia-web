from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

CREDENTIALS = {"email": "supervisor@example.com", "password": "Secret123"}


def test_register(fake_supabase):
    response = client.post("/register", json=CREDENTIALS)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == CREDENTIALS["email"]
    assert body["rol"] == "supervisor"

    row = fake_supabase.store["usuarios"][0]
    assert row["email"] == CREDENTIALS["email"]
    assert row["rol"] == "supervisor"
    assert row["nombre"] == "supervisor"


def test_login(fake_supabase):
    assert client.post("/register", json=CREDENTIALS).status_code == 200
    response = client.post(
        "/login",
        json={"email": CREDENTIALS["email"], "password": CREDENTIALS["password"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == CREDENTIALS["email"]


def test_login_invalid_credentials(fake_supabase):
    response = client.post(
        "/login", json={"email": CREDENTIALS["email"], "password": "wrong"}
    )
    assert response.status_code == 401


def test_protected_endpoints_require_token():
    upload = client.post("/upload", files={"file": ("x.png", b"fake", "image/png")})
    results = client.get("/results/x.png")
    assert upload.status_code == 401
    assert results.status_code == 401


def test_protected_endpoint_rejects_invalid_token():
    response = client.post(
        "/upload",
        files={"file": ("x.png", b"fake", "image/png")},
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401
