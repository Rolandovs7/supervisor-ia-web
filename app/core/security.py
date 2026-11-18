"""JWT authentication via Supabase Auth."""

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.database import get_client

_bearer = HTTPBearer(auto_error=False)
_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token de autenticación inválido o ausente",
    headers={"WWW-Authenticate": "Bearer"},
)


def validate_token(token: str | None) -> Any:
    """Validate a raw JWT through Supabase Auth (shared by HTTP and WS)."""
    if not token:
        raise _UNAUTHORIZED

    try:
        response = get_client().auth.get_user(token)
    except Exception as exc:
        raise _UNAUTHORIZED from exc

    user = getattr(response, "user", None)
    if user is None:
        raise _UNAUTHORIZED
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Any:
    """Resolve a ``Bearer`` JWT through Supabase and return the auth user."""
    return validate_token(credentials.credentials if credentials else None)
