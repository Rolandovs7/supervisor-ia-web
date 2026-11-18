"""Construction site management."""

import re
from datetime import date
from io import BytesIO
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.security import get_current_user
from app.models.schemas import ObraCreate, ObraResponse
from app.services.database import create_obra, get_alertas, get_obra, get_obras
from app.services.reports import build_obra_report

router = APIRouter(prefix="/obras", tags=["obras"])


@router.post("", response_model=ObraResponse)
async def create_obra_endpoint(
    payload: ObraCreate, user: Any = Depends(get_current_user)
) -> dict[str, Any]:
    """Create a construction site."""
    row = payload.model_dump(exclude_none=True)
    # PostgREST's JSON encoder does not handle datetime.date objects.
    for key in ("fecha_inicio", "fecha_fin"):
        if isinstance(row.get(key), date):
            row[key] = row[key].isoformat()
    return create_obra(row)


@router.get("", response_model=list[ObraResponse])
async def list_obras(user: Any = Depends(get_current_user)) -> list[dict[str, Any]]:
    """List every construction site."""
    return get_obras()


@router.get("/{obra_id}", response_model=ObraResponse)
async def get_obra_endpoint(
    obra_id: str, user: Any = Depends(get_current_user)
) -> dict[str, Any]:
    """Return one construction site or 404."""
    obra = get_obra(obra_id)
    if obra is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Obra no encontrada"
        )
    return obra


@router.get("/{obra_id}/reporte")
async def descargar_reporte(
    obra_id: str, user: Any = Depends(get_current_user)
) -> StreamingResponse:
    """Generate and stream a downloadable PDF safety report for one obra."""
    obra = get_obra(obra_id)
    if obra is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Obra no encontrada"
        )

    pdf = build_obra_report(obra, get_alertas(obra_id))
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "-", str(obra.get("nombre") or "obra")).strip("-")
    filename = f"reporte-{safe_name or 'obra'}.pdf"

    return StreamingResponse(
        BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
