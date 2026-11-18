"""Safety alert querying and resolution."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.schemas import AlertaResponse
from app.services.database import get_alertas, resolver_alerta

router = APIRouter(prefix="/alertas", tags=["alertas"])


@router.get("", response_model=list[AlertaResponse])
async def list_alertas(
    obra_id: str | None = None, user: Any = Depends(get_current_user)
) -> list[dict[str, Any]]:
    """List alerts, optionally filtered by construction site."""
    return get_alertas(obra_id)


@router.put("/{alerta_id}/resolver", response_model=AlertaResponse)
async def resolve_alerta(
    alerta_id: str, user: Any = Depends(get_current_user)
) -> dict[str, Any]:
    """Mark an alert as resolved."""
    try:
        return resolver_alerta(alerta_id)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Alerta no encontrada"
        ) from exc
