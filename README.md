# Supervisor IA — Supervisor Inteligente de Obras con IA

Plataforma full-stack para la supervisión de seguridad en obras de construcción. Combina visión por computadora, alertas en tiempo real y evidencia offline-first para que un supervisor pueda detectar personas y verificar el uso de equipo de protección personal (EPI), registrar obras, resolver alertas y descargar reportes PDF.

## Componentes

| Directorio | Tecnología | Función |
| --- | --- | --- |
| Raíz | FastAPI + SQLAlchemy-free (Supabase) | API REST, autenticación JWT, WebSockets, procesamiento de imágenes y reportes PDF |
| `frontend/` | React 19 + Vite + TypeScript + TailwindCSS | Panel web SaaS de administración |
| `movil/` | Flutter 3 + Dart | App móvil offline-first para capturar evidencia y sincronizarla |

**Flujo principal:** el usuario sube una imagen (desde el panel web o la app móvil) → se guarda en Cloudinary → YOLOv8 detecta personas → un modelo de EPI detecta casco y chaleco → se persisten el análisis y las alertas en Supabase → se emiten alertas por WebSocket → el supervisor las consulta, resuelve y exporta en PDF.

## Requisitos previos

- Python 3.12 con `venv` y `pip`.
- Node.js 20+ y `npm`.
- Flutter 3.47 / Dart 3.13 y Android SDK (solo para la app móvil).
- Un proyecto de Supabase con Auth habilitado y acceso a la base de datos; `psql` disponible para aplicar el esquema.
- Credenciales de Cloudinary para almacenar imágenes de forma permanente.
- Conexión a internet para descargar dependencias y los pesos de los modelos.

## Configuración

Crea un archivo `.env` en la raíz con tus propias credenciales (este archivo está ignorado por Git). Las variables utilizadas son:

- `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
- `SUPABASE_DB_URL` (usado por `init_db.py` para crear las tablas)
- `CLOUDINARY_URL` o `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
- `FRONTEND_ORIGINS` (opcional; orígenes de producción separados por comas)

Para el frontend, copia `frontend/.env.example` a `frontend/.env` y ajusta `VITE_API_URL` si el backend no está en `http://localhost:8000`.

> No versiones archivos `.env` reales ni credenciales. Solo se versionan los ejemplos (`*.env.example`).

### Modelos de IA

`yolov8n.pt` (personas) se descarga automáticamente en la primera inferencia. El modelo de EPI debe descargarse una vez:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
from huggingface_hub import hf_hub_download

origen = hf_hub_download(
    repo_id="wntrsldr/yolov8n-ppe-detection-6classes",
    filename="best.pt",
)
Path(origen).replace("ppe_model.pt")
PY
```

Ambos archivos `.pt` quedan en la raíz y están ignorados por Git.

## Backend

```bash
python3.12 -m venv .venv
./.venv/bin/pip install --no-cache-dir -r requirements.txt \
  --extra-index-url https://download.pytorch.org/whl/cpu

./.venv/bin/python init_db.py     # aplica el esquema en Supabase
./.venv/bin/python main.py        # uvicorn con reload en http://localhost:8000
```

El wheel local de `vendor/` garantiza que `opencv-python-headless` sea quien proporcione `cv2` (evita errores de GUI en servidores). El `--extra-index-url` ya está declarado en `requirements.txt`, así que en Render no hace falta repetirlo.

## Frontend web

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

El panel usa el JWT devuelto por `/login`, guardado en `localStorage`, y se conecta a `ws://localhost:8000/ws/alertas` para el feed en vivo.

## App móvil

```bash
cd movil
flutter pub get
flutter run                 # requiere emulador/dispositivo Android
flutter build apk --debug   # genera build/app/outputs/apk/debug/app-debug.apk
```

`lib/config.dart` define `apiUrl = 'http://10.0.2.2:8000'`, la dirección con la que el emulador de Android alcanza el backend del equipo host. En un dispositivo físico o en producción, cámbiala por la IP/dominio correspondiente. La app guarda las fotos en SQLite y las sube cuando hay conexión y hay sesión activa.

## Despliegue en Render

El blueprint `render.yaml` define un Web Service de Python en la raíz del repo:

- Build: `pip install -r requirements.txt` (el archivo incluye el `--extra-index-url` de PyTorch CPU).
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- Health check: `GET /`.
- Versiones y secretos: `PYTHON_VERSION=3.12.3`; el resto de variables (`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_DB_URL`, `CLOUDINARY_*`, `FRONTEND_ORIGINS`) se declaran con `sync: false` y se completan en el dashboard de Render. `SUPABASE_DB_URL` solo hace falta si se ejecuta `init_db.py` desde Render.

Los archivos `.pt` no se versionan: `app/services/analysis.py:ensure_models()` los descarga al arrancar (y vuelve a intentarlo en la primera inferencia si falló el arranque). `yolov8n.pt` se obtiene de los assets públicos de Ultralytics y `ppe_model.pt` del repo `wntrsldr/yolov8n-ppe-detection-6classes` en Hugging Face.

`vendor/opencv_python-5.0.0.93-py3-none-any.whl` es un meta-paquete local con el nombre de distribución que exige Ultralytics; instala solo `opencv-python-headless`, evitando dependencias GUI/Qt en el servidor.

## Verificación

```bash
# Backend
./.venv/bin/pip install -r requirements-dev.txt   # incluye pytest; Render no lo instala
pytest -q
./.venv/bin/pip check

# Web
cd frontend && npm run build

# Móvil
cd movil && flutter analyze
```

## Notas

- Todas las rutas excepto `/`, `/register` y `/login` requieren un token Bearer válido de Supabase Auth.
- El resultado de cada análisis también se mantiene en memoria en `analysis_results` (se pierde al reiniciar el backend).
- Las imágenes se suben a Cloudinary en segundo plano; el archivo temporal se elimina al finalizar el análisis.
