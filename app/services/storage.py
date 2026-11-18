"""Temporary image storage and permanent Cloudinary uploads."""

import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

from app.core.config import settings

_CHUNK_SIZE = 1024 * 1024
_FOLDER = "supervisor-ia"


async def save_temporary(file: UploadFile) -> Path:
    """Stream an uploaded image to a temp file and return its path."""
    suffix = Path(file.filename or "").suffix or ".img"
    fd, name = tempfile.mkstemp(
        prefix="supervisor-", suffix=suffix, dir=settings.temp_dir
    )
    path = Path(name)
    try:
        with os.fdopen(fd, "wb") as destination:
            while chunk := await file.read(_CHUNK_SIZE):
                destination.write(chunk)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()
    return path


def upload_to_cloudinary(image_path: Path) -> str:
    """Upload a local image to Cloudinary and return its ``secure_url``."""
    if settings.cloudinary_url:
        parsed = urlparse(settings.cloudinary_url)
        cloud_name, api_key, api_secret = (
            parsed.hostname,
            parsed.username,
            parsed.password,
        )
    else:
        cloud_name = settings.cloudinary_cloud_name
        api_key = settings.cloudinary_api_key
        api_secret = settings.cloudinary_api_secret

    if not all((cloud_name, api_key, api_secret)):
        raise RuntimeError("Faltan credenciales de Cloudinary en .env")

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )
    result = cloudinary.uploader.upload(
        str(image_path), resource_type="image", folder=_FOLDER
    )
    return result["secure_url"]
