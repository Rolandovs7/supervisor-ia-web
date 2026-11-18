"""Request and response schemas."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr


class UploadResponse(BaseModel):
    """Acknowledgement sent before the background analysis finishes."""

    filename: str
    status: Literal["queued"] = "queued"
    temp_path: str
    obra_id: str | None = None


class ObraCreate(BaseModel):
    """Payload for creating a construction site."""

    nombre: str
    ubicacion: str | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None


class ObraResponse(BaseModel):
    id: str
    nombre: str
    ubicacion: str | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    id: str
    email: str
    rol: str = "supervisor"


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class AlertaResponse(BaseModel):
    id: str
    obra_id: str | None = None
    analisis_id: str | None = None
    imagen_id: str | None = None
    tipo: str
    descripcion: str
    nivel: str = "baja"
    resuelta: bool = False
    created_at: datetime | None = None
