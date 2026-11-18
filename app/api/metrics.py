"""Dashboard counters."""

from typing import Any

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.services.database import get_metrics

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def metrics(user: Any = Depends(get_current_user)) -> dict[str, int]:
    """Return the numbers shown on the dashboard metric cards."""
    return get_metrics()
