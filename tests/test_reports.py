from fastapi.testclient import TestClient

from app.services import database
from main import app

client = TestClient(app)

OBRA = {"nombre": "Torre Norte", "ubicacion": "Av. Principal 123"}


def test_descargar_reporte_pdf(fake_supabase, auth_headers):
    obra = client.post("/obras", json=OBRA, headers=auth_headers).json()
    database.create_alerta(
        "seguridad",
        "Personas detectadas en la imagen",
        nivel="baja",
        obra_id=obra["id"],
    )

    response = client.get(f"/obras/{obra['id']}/reporte", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].startswith("attachment; filename=")
    assert "reporte-" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-")
    assert len(response.content) > 1000
    assert len(fake_supabase.store["alertas"]) == 1


def test_reporte_pdf_obra_not_found(auth_headers):
    response = client.get("/obras/no-existe/reporte", headers=auth_headers)
    assert response.status_code == 404


def test_reporte_pdf_requires_token():
    assert client.get("/obras/obras-1/reporte").status_code == 401
