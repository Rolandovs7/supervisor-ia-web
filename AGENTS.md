# AGENTS.md

## Layout
- FastAPI app: `main.py` owns the app and `GET /` healthcheck; `app/api/routes.py` has `POST /upload` and `GET /results/{filename}`. Other routers: `app/api/auth.py` (`/register`, `/login`), `app/api/obras.py` (`/obras`), `app/api/alertas.py` (`/alertas`), `app/api/websockets.py` (`/ws/alertas`). Add endpoints to a router, not `main.py`.
- `app/services/`: `storage.py` (temp files + Cloudinary upload), `analysis.py` (YOLOv8 + persistence), `database.py` (Supabase client + CRUD). Schemas in `app/models/schemas.py`, env settings in `app/core/config.py`.
- `init_db.py` is a one-off DDL bootstrap (psql, idempotent); `.env` and `*.pt` are gitignored.

## Supabase
- `.env` has `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` (new `sb_secret_` key) and `SUPABASE_DB_URL` (postgres connection string).
- The `sb_secret_` key works for the Data API (PostgREST) but **cannot create tables**: Management API returns 401 and there is no `exec_sql` RPC. Use `init_db.py` with `SUPABASE_DB_URL` for schema changes.
- For this project the direct port 5432 is refused; `init_db.py` strips the `[...]` password placeholder and falls back to port 6543 on `db.<ref>.supabase.co` with user `postgres`. Keep that fallback.
- Tables: `usuarios` (with `rol`, default `supervisor`), `obras` (with `fecha_inicio` + `fecha_fin`), `imagenes` (with `temp_path`, `secure_url`, `obra_id`), `analisis`, `alertas` (with `obra_id`, `descripcion`, `nivel`, `resuelta`; legacy nullable `mensaje`), `logs`. `POST /upload` inserts the `imagenes` row; the background task inserts `analisis` and an `alerta` when people are detected.
- Auth: Supabase Auth via `auth.sign_up` / `auth.sign_in_with_password`; `app/core/security.py:get_current_user` validates the Bearer JWT with `auth.get_user()` (no local decoding; `python-jose` + `passlib` are installed only as a fallback). All endpoints except `/`, `/register`, `/login` require the token.

## Obras and alerts
- `POST /obras` accepts `nombre`, `ubicacion`, `fecha_inicio`, `fecha_fin` (dates are converted to ISO strings before hitting PostgREST); `GET /obras` lists and `GET /obras/{obra_id}` returns 404 when missing.
- `POST /upload` takes an optional `obra_id` from form data or query string; it is stored on the `imagenes` row and forwarded to `analyze_image()` so the generated alert carries it too.
- `create_alerta(tipo, descripcion, nivel, obra_id, analisis_id, imagen_id)` in `database.py` is the alert seam. YOLO + people detected → `tipo='seguridad'`, `descripcion='Personas detectadas en la imagen'`, `nivel='baja'`, `resuelta=False`. `GET /alertas?obra_id=...` filters; `PUT /alertas/{id}/resolver` sets `resuelta=true` (404 if the row does not exist).
- `AlertaResponse` must include `created_at` — the DB returns it via `select("*")`, but FastAPI drops any field absent from `response_model`. The frontend formats it with `new Date(value).toLocaleString('es-PE', …)` in `src/lib/utils.ts`.

## PPE detection
- `ppe_model.pt` lives in the repo root (gitignored by `*.pt`). `app/services/analysis.py` downloads missing weights automatically: `_download_person_model()` fetches `yolov8n.pt` from `https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt`, and `_download_ppe_model()` uses `hf_hub_download(repo_id="wntrsldr/yolov8n-ppe-detection-6classes", filename="best.pt")` then copies it to `ppe_model.pt`. `ensure_models()` runs in the FastAPI lifespan (`main.py`) and failures are only logged; the lazy loaders retry on first inference. `huggingface_hub`, `hf-xet` and `tqdm` are pinned in `requirements.txt`.
- `app/services/analysis.py` loads two lazy models from absolute paths: `get_model()` (`yolov8n.pt`, COCO `person`) and `get_ppe_model()` (`ppe_model.pt`). Its labels are `Gloves, Vest, goggles, helmet, mask, safety_shoe`; `_extract()` lowercases them, so `Vest` → `vest`.
- Deployment: `render.yaml` defines a free Python web service with `pip install -r requirements.txt` / `uvicorn main:app --host 0.0.0.0 --port $PORT`; secrets use `sync: false`. `requirements.txt` includes the PyTorch CPU `--extra-index-url` and excludes test packages; `requirements-dev.txt` adds pytest for local runs.
- `vendor/opencv_python-5.0.0.93-py3-none-any.whl` is a checked-in metadata-only shim named `opencv-python` that depends on `opencv-python-headless`; `requirements.txt` references the wheel instead of the GUI wheel. Installing both official OpenCV wheels always leaves Qt/GUI `cv2` in control, even if headless is listed last, which breaks headless servers. It was built from a PEP 621 project declaring name `opencv-python`, version `5.0.0.93` and dependency `opencv-python-headless==5.0.0.93`.
- PPE inference runs on the same image after the person pass; its boxes are appended to `detections` and `ppe_model` is added to the result payload. A PPE failure logs a warning, disables missing-PPE alerts, and keeps the person pipeline alive.
- With people present, the low `Personas detectadas en la imagen` alert is always created; if helmets < people (`faltan_epis`), a second `nivel='alta'` alert says `Posible falta de casco detectada`, appending ` y falta de chaleco` when vests < people too. Both are broadcast. Tests mock both models via `tests/test_api.py:_mock_pipeline(person_count=..., ppe_classes=...)`.

## PDF reports
- `reportlab` is pinned in `requirements.txt` (installed with `--no-cache-dir`). `app/services/reports.py:build_obra_report(obra, alertas)` returns PDF bytes built in memory: obra header + summary + alerts table (`fecha`, `tipo`, `nivel`, `estado`); `created_at` is rendered `dd/mm/yyyy HH:MM`.
- `GET /obras/{obra_id}/reporte` in `app/api/obras.py` is protected, 404s on missing obra, calls `get_alertas(obra_id)` and streams the bytes with `StreamingResponse(BytesIO(pdf), media_type="application/pdf")` plus a sanitized `Content-Disposition: attachment; filename="reporte-<obra>.pdf"`.
- Frontend: `obrasApi.downloadReport()` requests the PDF with `responseType: 'blob'`, uses the server filename (slug fallback) and triggers an anchor download. The button "Descargar Reporte PDF" lives on each card in `frontend/src/pages/Obras.tsx`.

## WebSockets
- `app/api/websockets.py` owns `ConnectionManager` (singleton `manager`) and `WS /ws/alertas?token=<JWT>`. Auth reuses `security.validate_token()`: invalid/missing token → close with code 1008 **before** `accept()`.
- The endpoint accepts, stores the connection and loops on `receive_text()` until `WebSocketDisconnect`, then removes it from `manager.active_connections`.
- `analyze_image()` runs in a worker thread, so after `create_alerta()` it calls `manager.broadcast_threadsafe({"type": "alerta", "alerta": alerta})`. The manager captures the running loop in `connect()` and schedules `broadcast()` with `asyncio.run_coroutine_threadsafe()`. Never call `broadcast()` directly from the sync background task.

## Cloudinary
- Credentials are supplied by the user in `.env` and read through `app/core/config.py`; `storage.upload_to_cloudinary()` prefers `CLOUDINARY_URL`, falling back to the three individual keys. Never hardcode or echo their values.
- Background order: upload to Cloudinary → `update_imagen_url()` → YOLO inference → temp file cleanup (in `analyze_image`'s `finally`). The upload folder is `supervisor-ia` and the returned `secure_url` is stored both in `analysis_results[filename]` and in Supabase.
- Results are also kept in `analysis_results[filename]` (in-memory: lost on restart, same filename overwrites).

## Analysis pipeline
- `yolov8n.pt` is loaded lazily by `get_model()` and auto-downloads into the repo root on first real inference; the relative path is CWD-dependent, so run from here.
- Only COCO `person` is counted. `extract_ppe_detections()` is the seam for a future custom helmet/vest model.
- Background tasks run in a worker thread; keep inference out of the request path and keep temp-file cleanup in `analyze_image`'s `finally`.

## Python environment
- Use `.venv/bin/python` (3.12.3) and `.venv/bin/pip` explicitly; don't rely on shell activation or system/conda Python.
- `requirements.txt` is an alphabetized, fully pinned freeze. Keep new pins exact and alphabetized. Its `+cpu` torch wheels aren't on plain PyPI: fresh installs need `--extra-index-url https://download.pytorch.org/whl/cpu`.
- `ultralytics` requires the `opencv-python` distribution name; `requirements.txt` installs the local metadata-only wheel from `vendor/` plus `opencv-python-headless`, so no GUI `cv2` is installed. Verify with `cv2.getBuildInformation()` → `GUI: NONE`. Installing `supabase` downgrades `websockets` to 15.0.1.

## CORS
- `main.py` installs `CORSMiddleware` with explicit origins: `http://localhost:5173`, `http://127.0.0.1:5173`, the production Cloudflare Pages URL `https://supervisor-ia-web.pages.dev`, plus any comma-separated `FRONTEND_ORIGINS` env var (read via `app/core/config.py`) for extra origins. Never use `allow_origins=["*"]` together with `allow_credentials=True`.
- `allow_methods=["*"]`, `allow_headers=["*"]`, `allow_credentials=True`. Keep the middleware registered before the routers so `OPTIONS /login` is answered with 200 instead of 405.

## Frontend
- `frontend/` is a Vite + React 19 + TypeScript + TailwindCSS 3 app. Use `npm` from that directory (`npm install`, `npm run build`, `npm run lint`); `npm run build` runs `tsc -b && vite build` and must stay clean.
- `tsconfig.app.json` enables `verbatimModuleSyntax`, `erasableSyntaxOnly` and `noUnusedLocals`: use `import type`, no enums/parameter properties, and avoid unused symbols.
- API base URL comes from `VITE_API_URL` (default `http://localhost:8000`); `frontend/.env.example` documents it and `frontend/.env.production` points to the Render service `https://supervisor-api-g7dk.onrender.com` (public URL, not a secret, so it is un-ignored in the root `.gitignore`). The JWT is stored in `localStorage` and injected by `src/lib/api.ts`.
- Auth/Theme/WebSocket live in context providers; `useWebSocket` reconnects with exponential backoff (max 30s). Dark theme is the default.
- The dashboard reads `GET /metrics` (protected) added to the backend for the three metric cards. `frontend/node_modules`, `frontend/dist` and `frontend/.env` are gitignored.

## Mobile app (Flutter)
- `movil/` was created from the repo root with `flutter create --org com.supervisor_ia movil` (Flutter 3.47.2 / Dart 3.13.2). Use plain `flutter`/`dart` commands from that directory; `flutter pub get`, `flutter analyze` and `flutter build apk --debug` must stay clean.
- Dependencies in `movil/pubspec.yaml`: `http`, `sqflite`, `path`, `shared_preferences`, `image_picker`, `connectivity_plus`, `path_provider` (added via `flutter pub add`, pinned with `^` constraints).
- `movil/lib/config.dart` holds `const String apiUrl = 'http://10.0.2.2:8000'` (Android emulator alias for host localhost). Change it for a real device or production.
- `movil/lib/models/foto_pendiente.dart` defines `FotoPendiente(id, path, obraId, timestamp, sincronizada)` with `toMap`/`fromMap`; `id` is an `int?` because SQLite uses `INTEGER PRIMARY KEY AUTOINCREMENT`.
- `db_service.dart` lazily opens `<documents>/supervisor_ia.db` (singleton), creates `fotos_pendientes(id, path, obra_id, timestamp, sincronizada)` and exposes `inicializarDb()`, `insertarFoto()`, `obtenerFotosPendientes()` (only `sincronizada = 0`) and `marcarComoSincronizada(id)`. `main()` calls `inicializarDb()` before `runApp()`.
- `auth_service.dart` stores the JWT in SharedPreferences under `supervisor_ia_token`; `login_screen.dart` POSTs `/login`, saves it and pushes `CapturaScreen`. `sync_service.dart:sincronizarFotos()` checks `connectivity_plus`, reads pending photos and POSTs multipart `file` (+ optional `obra_id`) to `/upload` with the Bearer token, marking each 200 as synchronized.
- `captura_screen.dart` uses `image_picker` (camera), copies the image into the documents directory, inserts the pending row, shows the success snackbar and refreshes a `FutureBuilder` list; "Sincronizar Ahora" calls `sincronizarFotos()`.
- Keep comments in comment-only Dart files as `//`, not `///`: top-level doc comments without a `library;` directive trigger `dangling_library_doc_comments` in `flutter analyze`. The default `test/widget_test.dart` was rewritten for `SupervisorApp` instead of the template's `MyApp`.

- CI: `.github/workflows/build_apk.yml` builds the APK on pushes to `main` that touch `movil/**` (checkout@v4, setup-java@v4 temurin 17, subosito/flutter-action@v2 stable, `flutter pub get`, `flutter build apk --release`, upload-artifact@v4). The artifact path covers both `build/app/outputs/flutter-apk/` and the legacy `build/app/outputs/apk/release/`.

## Run / verify
- Start with `./.venv/bin/python main.py` (uvicorn + reload on :8000). Run `pytest -v` (43 tests); `tests/conftest.py` fakes the Supabase client (including Auth), the YOLO model and the Cloudinary uploader is monkeypatched, so tests need no network. `tests/test_websockets.py` uses `TestClient.websocket_connect`.
- Check the environment with `./.venv/bin/pip check`. No CI or lint/typecheck config yet.
