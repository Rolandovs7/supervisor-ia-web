import io
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from app.services import analysis
from main import app

client = TestClient(app)

SECURE_URL = "https://res.cloudinary.com/demo/image/upload/supervisor-ia/test.png"


PPE_NAMES = {
    0: "Gloves",
    1: "Vest",
    2: "goggles",
    3: "helmet",
    4: "mask",
    5: "safety_shoe",
}
PPE_INDEX = {name.lower(): index for index, name in PPE_NAMES.items()}


class _FakeBox:
    def __init__(self, cls, conf=0.97, xyxy=(3.0, 4.0, 20.0, 21.0)):
        self.cls = [cls]
        self.conf = [conf]
        self.xyxy = [list(xyxy)]


class _FakeResult:
    def __init__(self, names, boxes):
        self.names = names
        self.boxes = boxes


class _FakeModel:
    def __init__(self, results):
        self.results = results

    def __call__(self, path, verbose=False):
        return self.results


def _person_result(count=1):
    return _FakeResult({0: "person"}, [_FakeBox(0) for _ in range(count)])


def _ppe_result(*classes):
    return _FakeResult(PPE_NAMES, [_FakeBox(PPE_INDEX[name.lower()]) for name in classes])


def _dummy_png() -> bytes:
    image = Image.fromarray(np.zeros((32, 32, 3), dtype=np.uint8))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _upload(filename: str, headers: dict, **kwargs):
    return client.post(
        "/upload",
        files={"file": (filename, _dummy_png(), "image/png")},
        headers=headers,
        **kwargs,
    )


def _mock_pipeline(monkeypatch, person_count=1, ppe_classes=("helmet", "Vest")):
    monkeypatch.setattr(analysis, "_model", _FakeModel([_person_result(person_count)]))
    monkeypatch.setattr(analysis, "_ppe_model", _FakeModel([_ppe_result(*ppe_classes)]))
    monkeypatch.setattr(analysis, "upload_to_cloudinary", lambda path: SECURE_URL)


def test_healthcheck():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload(monkeypatch, fake_supabase, auth_headers):
    _mock_pipeline(monkeypatch)
    response = _upload("upload_test.png", auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "queued"

    imagen = fake_supabase.store["imagenes"][0]
    assert imagen["filename"] == "upload_test.png"
    assert imagen["temp_path"] == response.json()["temp_path"]
    assert imagen["secure_url"] == SECURE_URL
    assert not Path(response.json()["temp_path"]).exists()


def test_results(monkeypatch, fake_supabase, auth_headers):
    _mock_pipeline(monkeypatch)
    assert _upload("results_test.png", auth_headers).status_code == 200

    response = client.get("/results/results_test.png", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["person_count"] == 1
    assert response.json()["detections"][0]["class"] == "person"
    assert response.json()["secure_url"] == SECURE_URL

    assert len(fake_supabase.store["analisis"]) == 1
    assert fake_supabase.store["analisis"][0]["person_count"] == 1

    alerta = fake_supabase.store["alertas"][0]
    assert alerta["tipo"] == "seguridad"
    assert alerta["descripcion"] == "Personas detectadas en la imagen"
    assert alerta["nivel"] == "baja"
    assert alerta["resuelta"] is False


def test_upload_with_obra_id_form(monkeypatch, fake_supabase, auth_headers):
    _mock_pipeline(monkeypatch)
    response = _upload(
        "con_obra.png", auth_headers, data={"obra_id": "obras-1"}
    )
    assert response.status_code == 200
    assert response.json()["obra_id"] == "obras-1"
    assert fake_supabase.store["imagenes"][0]["obra_id"] == "obras-1"
    assert fake_supabase.store["alertas"][0]["obra_id"] == "obras-1"


def test_upload_with_obra_id_query(monkeypatch, fake_supabase, auth_headers):
    _mock_pipeline(monkeypatch)
    response = _upload("por_query.png", auth_headers, params={"obra_id": "obras-9"})
    assert response.status_code == 200
    assert fake_supabase.store["imagenes"][0]["obra_id"] == "obras-9"


def test_results_not_found(auth_headers):
    response = client.get("/results/does-not-exist.png", headers=auth_headers)
    assert response.status_code == 404


def test_ppe_detecciones_guardadas_en_resultados(monkeypatch, fake_supabase, auth_headers):
    _mock_pipeline(monkeypatch)
    assert _upload("ppe_detecciones.png", auth_headers).status_code == 200

    response = client.get("/results/ppe_detecciones.png", headers=auth_headers)
    payload = response.json()
    assert [item["class"] for item in payload["detections"]] == [
        "person",
        "helmet",
        "vest",
    ]
    assert payload["ppe_model"] == "ppe_model.pt"


def test_alerta_alta_sin_casco_y_chaleco(monkeypatch, fake_supabase, auth_headers):
    _mock_pipeline(monkeypatch, ppe_classes=())
    assert _upload(
        "ppe_sin_casco.png", auth_headers, data={"obra_id": "obras-7"}
    ).status_code == 200

    alertas = fake_supabase.store["alertas"]
    assert len(alertas) == 2
    alta = alertas[1]
    assert alta["nivel"] == "alta"
    assert alta["descripcion"] == "Posible falta de casco detectada y falta de chaleco"
    assert alta["obra_id"] == "obras-7"


def test_alerta_alta_por_proporcion_de_cascos(monkeypatch, fake_supabase, auth_headers):
    _mock_pipeline(
        monkeypatch,
        person_count=2,
        ppe_classes=("helmet", "Vest", "Vest"),
    )
    assert _upload("ppe_proporcion.png", auth_headers).status_code == 200

    alerta = fake_supabase.store["alertas"][1]
    assert alerta["nivel"] == "alta"
    assert alerta["descripcion"] == "Posible falta de casco detectada"


def test_sin_alerta_alta_si_hay_casco(monkeypatch, fake_supabase, auth_headers):
    _mock_pipeline(monkeypatch, ppe_classes=("helmet",))
    assert _upload("ppe_con_casco.png", auth_headers).status_code == 200

    alertas = fake_supabase.store["alertas"]
    assert len(alertas) == 1
    assert alertas[0]["nivel"] == "baja"


def test_sin_alertas_sin_personas(monkeypatch, fake_supabase, auth_headers):
    _mock_pipeline(monkeypatch, person_count=0, ppe_classes=())
    assert _upload("ppe_sin_personas.png", auth_headers).status_code == 200

    assert fake_supabase.store["alertas"] == []
