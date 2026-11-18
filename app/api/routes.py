"""HTTP routes."""

from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)

from app.core.security import get_current_user
from app.models.schemas import UploadResponse
from app.services.analysis import analysis_results, analyze_image
from app.services.database import save_imagen
from app.services.storage import save_temporary

router = APIRouter(tags=["uploads"])


@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    obra_id: str | None = Form(None),
    user: Any = Depends(get_current_user),
) -> UploadResponse:
    """Register the image, save it to a temp file and queue the analysis."""
    obra_id = obra_id or request.query_params.get("obra_id")
    filename = file.filename or "unknown"
    image_path = await save_temporary(file)
    try:
        imagen = save_imagen(filename, str(image_path), obra_id)
    except Exception:
        image_path.unlink(missing_ok=True)
        raise

    background_tasks.add_task(
        analyze_image, image_path, filename, imagen["id"], obra_id
    )
    return UploadResponse(
        filename=filename, temp_path=str(image_path), obra_id=obra_id
    )


@router.get("/results/{filename}")
async def get_results(
    filename: str, user: Any = Depends(get_current_user)
) -> dict[str, Any]:
    """Return the analysis JSON produced by the background task."""
    result = analysis_results.get(filename)
    if result is None:
        raise HTTPException(status_code=404, detail="No analysis for this filename")
    return result
