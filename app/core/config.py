"""Environment-driven settings (``SUPERVISOR_`` prefix + external service keys)."""

import tempfile
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """External keys are read verbatim from .env, without the prefix."""

    model_config = SettingsConfigDict(
        env_prefix="SUPERVISOR_",
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    temp_dir: Path = Path(tempfile.gettempdir())

    supabase_url: str = Field(alias="SUPABASE_URL")
    supabase_service_key: str = Field(alias="SUPABASE_SERVICE_KEY")

    # Optional until the .env is filled in; uploads fail loudly at call time.
    cloudinary_cloud_name: str = Field(default="", alias="CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: str = Field(default="", alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: str = Field(default="", alias="CLOUDINARY_API_SECRET")
    cloudinary_url: str = Field(default="", alias="CLOUDINARY_URL")

    # Comma-separated origins of the deployed frontend (e.g. https://app.example.com).
    cors_extra_origins: str = Field(default="", alias="FRONTEND_ORIGINS")


settings = Settings()
