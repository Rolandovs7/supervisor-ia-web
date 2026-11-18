from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

OBRA = {
    "nombre": "Torre Norte",
    "ubicacion": "Av. Principal 123",
    "fecha_inicio": "2026-01-10",
    "fecha_fin": "2026-12-20",
}


def test_create_obra(fake_supabase, auth_headers):
    response = client.post("/obras", json=OBRA, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["nombre"] == OBRA["nombre"]
    assert body["fecha_inicio"] == OBRA["fecha_inicio"]

    row = fake_supabase.store["obras"][0]
    assert row["nombre"] == OBRA["nombre"]
    assert row["fecha_fin"] == OBRA["fecha_fin"]


def test_list_and_get_obra(fake_supabase, auth_headers):
    created = client.post("/obras", json=OBRA, headers=auth_headers).json()

    listing = client.get("/obras", headers=auth_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    detail = client.get(f"/obras/{created['id']}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["nombre"] == OBRA["nombre"]


def test_get_obra_not_found(auth_headers):
    response = client.get("/obras/no-existe", headers=auth_headers)
    assert response.status_code == 404


def test_obras_require_token():
    assert client.get("/obras").status_code == 401
    assert client.post("/obras", json=OBRA).status_code == 401
