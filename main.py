"""FastAPI entrypoint for the construction-site supervision backend."""

import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.alertas import router as alertas_router
from app.api.auth import router as auth_router
from app.api.obras import router as obras_router
from app.api.metrics import router as metrics_router
from app.api.routes import router as api_router
from app.api.websockets import router as websockets_router
from app.core.config import settings
from app.services.analysis import ensure_models


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Fetch the gitignored model weights before the service accepts traffic."""
    await asyncio.to_thread(ensure_models)
    yield


app = FastAPI(title="Supervisor IA", version="0.1.0", lifespan=lifespan)

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://supervisor-ia-web.pages.dev",
    *[
        origin.strip()
        for origin in settings.cors_extra_origins.split(",")
        if origin.strip()
    ],
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def healthcheck() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(api_router)
app.include_router(obras_router)
app.include_router(alertas_router)
app.include_router(metrics_router)
app.include_router(websockets_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
