"""Registration and login backed by Supabase Auth."""

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.services.database import create_usuario, get_client

router = APIRouter(tags=["auth"])

DEFAULT_ROLE = "supervisor"


@router.post("/register", response_model=RegisterResponse)
async def register(payload: RegisterRequest) -> RegisterResponse:
    try:
        response = get_client().auth.sign_up(
            {"email": payload.email, "password": payload.password}
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail="No se pudo registrar") from exc
    user = response.user
    if user is None:
        raise HTTPException(status_code=400, detail="No se pudo crear el usuario")

    create_usuario(
        user_id=str(user.id),
        email=str(payload.email),
        nombre=payload.email.split("@")[0],
        rol=DEFAULT_ROLE,
    )
    return RegisterResponse(
        id=str(user.id), email=str(payload.email), rol=DEFAULT_ROLE
    )


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    try:
        response = get_client().auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas"
        ) from exc
    session = response.session
    user = response.user
    if session is None or not session.access_token or user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas"
        )

    return LoginResponse(
        access_token=session.access_token,
        user={"id": str(user.id), "email": str(user.email)},
    )
