import io

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from starlette.websockets import WebSocketDisconnect

from app.api.websockets import manager
from app.services import analysis
from main import app

client = TestClient(app)

SECURE_URL = "https://res.cloudinary.com/demo/image/upload/supervisor-ia/ws.png"


class _FakeBox:
    cls = [0]  # COCO class 0 == person
    conf = [0.98]
    xyxy = [[1.0, 2.0, 30.0, 31.0]]


class _FakeResult:
    names = {0: "person"}
    boxes = [_FakeBox()]


class _FakeModel:
    def __call__(self, path, verbose=False):
        return [_FakeResult()]


@pytest.fixture(autouse=True)
def clean_connections():
    manager.active_connections.clear()
    yield
    manager.active_connections.clear()


def _upload(headers):
    image = Image.fromarray(np.zeros((32, 32, 3), dtype=np.uint8))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return client.post(
        "/upload",
        files={"file": ("ws_test.png", buffer.getvalue(), "image/png")},
        headers=headers,
    )


def test_ws_broadcasts_alert(monkeypatch, fake_supabase, auth_headers):
    monkeypatch.setattr(analysis, "_model", _FakeModel())
    monkeypatch.setattr(analysis, "upload_to_cloudinary", lambda path: SECURE_URL)
    token = auth_headers["Authorization"].split(" ", 1)[1]

    with client.websocket_connect(f"/ws/alertas?token={token}") as websocket:
        assert _upload(auth_headers).status_code == 200
        message = websocket.receive_json()

    assert message["type"] == "alerta"
    alerta = message["alerta"]
    assert alerta["tipo"] == "seguridad"
    assert alerta["descripcion"] == "Personas detectadas en la imagen"
    assert alerta["nivel"] == "baja"
    assert alerta["resuelta"] is False
    assert alerta == fake_supabase.store["alertas"][0]


def test_ws_rejects_invalid_token(fake_supabase):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/alertas?token=not-a-real-token"):
            pass
