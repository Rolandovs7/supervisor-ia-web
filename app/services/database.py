"""Supabase persistence for images, analyses and safety alerts."""

from typing import Any

from supabase import Client, create_client

from app.core.config import settings

_client: Client | None = None


def get_client() -> Client:
    """Lazy client singleton, built from the ``sb_secret_`` service key."""
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client


def _insert(table: str, row: dict[str, Any]) -> dict[str, Any]:
    data = get_client().table(table).insert(row).execute().data
    if not data:
        raise RuntimeError(f"Supabase INSERT into {table} returned no rows")
    return data[0]


def create_usuario(
    user_id: str,
    email: str,
    nombre: str,
    rol: str = "supervisor",
) -> dict[str, Any]:
    """Mirror a Supabase Auth user into the app's ``usuarios`` table."""
    return _insert(
        "usuarios",
        {"id": user_id, "email": email, "nombre": nombre, "rol": rol},
    )


def get_metrics() -> dict[str, int]:
    """Aggregate dashboard counters from the existing tables."""
    client = get_client()
    obras = client.table("obras").select("id").execute().data
    alertas = client.table("alertas").select("id,resuelta").execute().data
    imagenes = client.table("imagenes").select("id,secure_url").execute().data
    return {
        "total_obras": len(obras),
        "alertas_pendientes": sum(not alerta.get("resuelta", False) for alerta in alertas),
        "imagenes_procesadas": sum(bool(image.get("secure_url")) for image in imagenes),
    }


def create_obra(row: dict[str, Any]) -> dict[str, Any]:
    """Create a construction site and return its row."""
    return _insert("obras", row)


def get_obras() -> list[dict[str, Any]]:
    """Return every construction site."""
    return get_client().table("obras").select("*").execute().data


def get_obra(obra_id: str) -> dict[str, Any] | None:
    """Return one construction site, or ``None`` when it does not exist."""
    data = get_client().table("obras").select("*").eq("id", obra_id).execute().data
    return data[0] if data else None


def save_imagen(
    filename: str, temp_path: str, obra_id: str | None = None
) -> dict[str, Any]:
    """Register an uploaded image and return its row (including ``id``)."""
    row: dict[str, Any] = {"filename": filename, "temp_path": temp_path}
    if obra_id:
        row["obra_id"] = obra_id
    return _insert("imagenes", row)


def update_imagen_url(imagen_id: str, secure_url: str) -> dict[str, Any]:
    """Store the permanent Cloudinary URL on an existing image row."""
    data = (
        get_client()
        .table("imagenes")
        .update({"secure_url": secure_url})
        .eq("id", imagen_id)
        .execute()
        .data
    )
    if not data:
        raise RuntimeError(f"Supabase UPDATE of imagenes/{imagen_id} returned no rows")
    return data[0]


def save_analisis(imagen_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Persist the YOLO result produced by the background task."""
    return _insert(
        "analisis",
        {
            "imagen_id": imagen_id,
            "modelo": payload["model"],
            "person_count": payload["person_count"],
            "detections": payload["detections"],
        },
    )


def get_analisis_by_imagen(imagen_id: str) -> list[dict[str, Any]]:
    """Return every analysis row associated with an image."""
    return (
        get_client()
        .table("analisis")
        .select("*")
        .eq("imagen_id", imagen_id)
        .execute()
        .data
    )


def create_alerta(
    tipo: str,
    descripcion: str,
    nivel: str = "baja",
    obra_id: str | None = None,
    analisis_id: str | None = None,
    imagen_id: str | None = None,
) -> dict[str, Any]:
    """Create a safety alert, optionally linked to an obra/analysis/image."""
    row: dict[str, Any] = {
        "tipo": tipo,
        "descripcion": descripcion,
        "nivel": nivel,
        "resuelta": False,
    }
    if obra_id:
        row["obra_id"] = obra_id
    if analisis_id:
        row["analisis_id"] = analisis_id
    if imagen_id:
        row["imagen_id"] = imagen_id
    return _insert("alertas", row)


def get_alertas(obra_id: str | None = None) -> list[dict[str, Any]]:
    """Return alerts, optionally filtered by construction site."""
    query = get_client().table("alertas").select("*")
    if obra_id:
        query = query.eq("obra_id", obra_id)
    return query.execute().data


def resolver_alerta(alerta_id: str) -> dict[str, Any]:
    """Mark an alert as resolved and return the updated row."""
    data = (
        get_client()
        .table("alertas")
        .update({"resuelta": True})
        .eq("id", alerta_id)
        .execute()
        .data
    )
    if not data:
        raise RuntimeError(f"Supabase UPDATE of alertas/{alerta_id} returned no rows")
    return data[0]

