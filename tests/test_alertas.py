from fastapi.testclient import TestClient

from app.services import database
from main import app

client = TestClient(app)


def _seed_alertas(fake_supabase):
    database.create_alerta("seguridad", "Faena A", obra_id="obras-1")
    database.create_alerta("seguridad", "Faena B", obra_id="obras-2")
    return fake_supabase.store["alertas"]


def test_list_alertas(fake_supabase, auth_headers):
    _seed_alertas(fake_supabase)
    response = client.get("/alertas", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["descripcion"] == "Faena A"
    assert response.json()[0]["resuelta"] is False


def test_list_alertas_includes_created_at(fake_supabase, auth_headers):
    fake_supabase.store["alertas"].append(
        {
            "id": "alertas-1",
            "obra_id": None,
            "tipo": "seguridad",
            "descripcion": "Faena A",
            "nivel": "baja",
            "resuelta": False,
            "created_at": "2026-11-18T02:29:57.932382+00:00",
        }
    )
    response = client.get("/alertas", headers=auth_headers)
    assert response.status_code == 200
    created_at = response.json()[0]["created_at"]
    assert created_at is not None
    assert "2026-11-18" in created_at


def test_list_alertas_filtered_by_obra(fake_supabase, auth_headers):
    _seed_alertas(fake_supabase)
    response = client.get("/alertas", params={"obra_id": "obras-2"}, headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["descripcion"] == "Faena B"


def test_resolver_alerta(fake_supabase, auth_headers):
    rows = _seed_alertas(fake_supabase)
    response = client.put(f"/alertas/{rows[0]['id']}/resolver", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["resuelta"] is True
    assert fake_supabase.store["alertas"][0]["resuelta"] is True
    assert fake_supabase.store["alertas"][1]["resuelta"] is False


def test_resolver_alerta_not_found(auth_headers):
    response = client.put("/alertas/no-existe/resolver", headers=auth_headers)
    assert response.status_code == 404


def test_alertas_require_token():
    assert client.get("/alertas").status_code == 401
    assert client.put("/alertas/x/resolver").status_code == 401
