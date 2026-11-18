from app.services import database


def test_create_obra_and_getters(fake_supabase):
    row = database.create_obra(
        {
            "nombre": "Torre Norte",
            "ubicacion": "Lima",
            "fecha_inicio": "2026-01-10",
        }
    )
    assert row["nombre"] == "Torre Norte"
    assert database.get_obras() == [row]
    assert database.get_obra(row["id"]) == row
    assert database.get_obra("no-existe") is None


def test_save_imagen(fake_supabase):
    row = database.save_imagen("obra.png", "/tmp/obra.png", obra_id="obras-1")
    assert row["filename"] == "obra.png"
    assert row["temp_path"] == "/tmp/obra.png"
    assert row["obra_id"] == "obras-1"
    assert fake_supabase.store["imagenes"] == [row]


def test_update_imagen_url(fake_supabase):
    imagen = database.save_imagen("faena.png", "/tmp/faena.png")
    updated = database.update_imagen_url(imagen["id"], "https://cdn.example/img.png")
    assert updated["secure_url"] == "https://cdn.example/img.png"
    assert fake_supabase.store["imagenes"][0]["secure_url"] == "https://cdn.example/img.png"


def test_save_and_get_analisis(fake_supabase):
    imagen = database.save_imagen("faena.png", "/tmp/faena.png")
    payload = {
        "model": "yolov8n.pt",
        "person_count": 2,
        "detections": [{"class": "person", "confidence": 0.9, "bbox": [0, 0, 1, 1]}],
    }
    saved = database.save_analisis(imagen["id"], payload)
    found = database.get_analisis_by_imagen(imagen["id"])
    assert found == [saved]
    assert found[0]["detections"] == payload["detections"]


def test_create_alerta(fake_supabase):
    alerta = database.create_alerta(
        "seguridad",
        "Personas detectadas en la imagen",
        obra_id="obras-1",
        analisis_id="analisis-1",
        imagen_id="imagenes-1",
    )
    assert alerta["tipo"] == "seguridad"
    assert alerta["nivel"] == "baja"
    assert alerta["resuelta"] is False
    assert alerta["obra_id"] == "obras-1"
    assert fake_supabase.store["alertas"] == [alerta]


def test_get_alertas_and_resolver(fake_supabase):
    database.create_alerta("seguridad", "Faena A", obra_id="obras-1")
    database.create_alerta("seguridad", "Faena B", obra_id="obras-2")

    assert len(database.get_alertas()) == 2
    filtradas = database.get_alertas("obras-1")
    assert len(filtradas) == 1
    assert filtradas[0]["descripcion"] == "Faena A"

    resuelta = database.resolver_alerta(filtradas[0]["id"])
    assert resuelta["resuelta"] is True
    assert fake_supabase.store["alertas"][0]["resuelta"] is True
