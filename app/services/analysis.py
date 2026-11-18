"""YOLOv8 inference and Supabase persistence for construction-site safety."""

import json
import shutil
import threading
import urllib.request
from pathlib import Path
from typing import Any

from huggingface_hub import hf_hub_download
from ultralytics import YOLO

from app.api.websockets import manager
from app.services.database import create_alerta, save_analisis, update_imagen_url
from app.services.storage import upload_to_cloudinary

ROOT = Path(__file__).resolve().parents[2]
MODEL_NAME = "yolov8n.pt"
PPE_MODEL_NAME = "ppe_model.pt"
MODEL_PATH = ROOT / MODEL_NAME
PPE_MODEL_PATH = ROOT / PPE_MODEL_NAME
MODEL_URL = (
    "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt"
)
PPE_REPO_ID = "wntrsldr/yolov8n-ppe-detection-6classes"
PPE_HUB_FILENAME = "best.pt"
PERSON_CLASSES = {"person"}
HELMET_CLASSES = {"helmet", "hard_hat"}
VEST_CLASSES = {"vest", "safety_vest"}
PPE_CLASSES = HELMET_CLASSES | VEST_CLASSES

_model: YOLO | None = None
_ppe_model: YOLO | None = None
_model_lock = threading.Lock()
_ppe_model_lock = threading.Lock()

# In-memory results keyed by the original uploaded filename.
analysis_results: dict[str, dict[str, Any]] = {}


def _download_person_model() -> None:
    """Fetch the COCO weights from Ultralytics when they are not bundled."""
    if MODEL_PATH.is_file():
        return
    print(f"[MODEL] Descargando {MODEL_NAME} desde Ultralytics", flush=True)
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)


def _download_ppe_model() -> None:
    """Fetch the six-class PPE weights from Hugging Face when not bundled."""
    if PPE_MODEL_PATH.is_file():
        return
    print(f"[MODEL] Descargando {PPE_MODEL_NAME} desde Hugging Face", flush=True)
    cached = Path(hf_hub_download(repo_id=PPE_REPO_ID, filename=PPE_HUB_FILENAME))
    shutil.copyfile(cached, PPE_MODEL_PATH)


def ensure_models() -> None:
    """Download missing weights at startup; failures are logged, not fatal.

    The lazy loaders retry on first inference, so a transient network error
    during boot does not take the whole service down.
    """
    for download in (_download_person_model, _download_ppe_model):
        try:
            download()
        except Exception as exc:
            print(f"[MODEL] WARN no se pudo descargar el modelo: {exc}", flush=True)


def get_model() -> YOLO:
    """Lazy, thread-safe loader (downloads ``yolov8n.pt`` on first use)."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _download_person_model()
                _model = YOLO(str(MODEL_PATH))
    return _model


def get_ppe_model() -> YOLO:
    """Lazy, thread-safe loader for the six-class PPE weights in the repo root."""
    global _ppe_model
    if _ppe_model is None:
        with _ppe_model_lock:
            if _ppe_model is None:
                _download_ppe_model()
                _ppe_model = YOLO(str(PPE_MODEL_PATH))
    return _ppe_model


def _extract(result: Any, allowed: set[str]) -> list[dict[str, Any]]:
    """Keep only the requested classes from one Ultralytics result."""
    detections: list[dict[str, Any]] = []
    for box in result.boxes:
        label = str(result.names[int(box.cls[0])]).lower()
        if label not in allowed:
            continue
        x1, y1, x2, y2 = (float(v) for v in box.xyxy[0])
        detections.append(
            {
                "class": label,
                "confidence": round(float(box.conf[0]), 4),
                "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
            }
        )
    return detections


def extract_ppe_detections(result: Any) -> list[dict[str, Any]]:
    """Keep helmet/vest boxes from the custom six-class PPE model.

    Its labels are ``Gloves, Vest, goggles, helmet, mask, safety_shoe``;
    ``_extract`` lowercases them so ``Vest`` becomes ``vest``.
    """
    return _extract(result, PPE_CLASSES)


def faltan_epis(disponibles: int, personas: int) -> bool:
    """True when there are fewer items than people (ratio below 1:1)."""
    return personas > 0 and disponibles < personas


def analyze_image(
    image_path: Path,
    filename: str,
    imagen_id: str,
    obra_id: str | None = None,
) -> dict[str, Any]:
    """Upload to Cloudinary, persist the URL, infer and clean up the temp file."""
    try:
        secure_url = upload_to_cloudinary(image_path)
        update_imagen_url(imagen_id, secure_url)

        results = get_model()(str(image_path), verbose=False)

        detections: list[dict[str, Any]] = []
        for result in results:
            detections.extend(_extract(result, PERSON_CLASSES))
        person_count = sum(d["class"] in PERSON_CLASSES for d in detections)

        # Run the PPE head on the same image; a failure must not kill the
        # person analysis, but it disables the missing-PPE alert logic.
        ppe_detections: list[dict[str, Any]] = []
        ppe_ok = True
        try:
            ppe_results = get_ppe_model()(str(image_path), verbose=False)
            for result in ppe_results:
                ppe_detections.extend(extract_ppe_detections(result))
        except Exception as exc:
            ppe_ok = False
            print(f"[PPE] WARN no se pudo ejecutar el modelo de EPI: {exc}", flush=True)
        detections.extend(ppe_detections)

        helmet_count = sum(d["class"] in HELMET_CLASSES for d in ppe_detections)
        vest_count = sum(d["class"] in VEST_CLASSES for d in ppe_detections)
        payload = {
            "filename": filename,
            "imagen_id": imagen_id,
            "secure_url": secure_url,
            "model": MODEL_NAME,
            "ppe_model": PPE_MODEL_NAME,
            "person_count": person_count,
            "detections": detections,
        }
        print(json.dumps(payload, indent=2), flush=True)
        analysis_results[filename] = payload

        alertas: list[dict[str, Any]] = []
        try:
            analisis = save_analisis(imagen_id, payload)
            if person_count:
                alertas.append(
                    create_alerta(
                        tipo="seguridad",
                        descripcion="Personas detectadas en la imagen",
                        nivel="baja",
                        obra_id=obra_id,
                        analisis_id=analisis["id"],
                        imagen_id=imagen_id,
                    )
                )
                if ppe_ok and faltan_epis(helmet_count, person_count):
                    descripcion = "Posible falta de casco detectada"
                    if faltan_epis(vest_count, person_count):
                        descripcion += " y falta de chaleco"
                    alertas.append(
                        create_alerta(
                            tipo="seguridad",
                            descripcion=descripcion,
                            nivel="alta",
                            obra_id=obra_id,
                            analisis_id=analisis["id"],
                            imagen_id=imagen_id,
                        )
                    )
        except Exception as exc:
            print(f"[DB] ERROR persistiendo el análisis: {exc}", flush=True)

        for alerta in alertas:
            manager.broadcast_threadsafe({"type": "alerta", "alerta": alerta})

        return payload
    finally:
        image_path.unlink(missing_ok=True)
