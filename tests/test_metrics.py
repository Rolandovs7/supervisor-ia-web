from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_metrics(fake_supabase, auth_headers):
    fake_supabase.store["obras"].append({"id": "obras-1"})
    fake_supabase.store["imagenes"].append(
        {"id": "imagenes-1", "secure_url": "https://cdn.example/a.png"}
    )
    fake_supabase.store["imagenes"].append({"id": "imagenes-2"})
    fake_supabase.store["alertas"].append({"id": "alertas-1", "resuelta": False})
    fake_supabase.store["alertas"].append({"id": "alertas-2", "resuelta": True})

    response = client.get("/metrics", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {
        "total_obras": 1,
        "alertas_pendientes": 1,
        "imagenes_procesadas": 1,
    }


def test_metrics_require_token():
    assert client.get("/metrics").status_code == 401
