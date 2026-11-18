"""One-off bootstrap: create the Supabase tables used by the backend.

Reads ``SUPABASE_DB_URL`` from .env and applies the DDL below with psql.
Safe to re-run: every statement uses IF NOT EXISTS.
"""

import subprocess
import sys
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent
DB_URL = dotenv_values(ROOT / ".env").get("SUPABASE_DB_URL")

SQL = """
CREATE TABLE IF NOT EXISTS usuarios (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre text NOT NULL,
    email text UNIQUE,
    rol text NOT NULL DEFAULT 'supervisor',
    created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS rol text NOT NULL DEFAULT 'supervisor';

CREATE TABLE IF NOT EXISTS obras (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre text NOT NULL,
    ubicacion text,
    fecha_inicio date,
    fecha_fin date,
    created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE obras ADD COLUMN IF NOT EXISTS fecha_inicio date;
ALTER TABLE obras ADD COLUMN IF NOT EXISTS fecha_fin date;

CREATE TABLE IF NOT EXISTS imagenes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    obra_id uuid REFERENCES obras(id) ON DELETE SET NULL,
    filename text NOT NULL,
    temp_path text,
    secure_url text,
    created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE imagenes ADD COLUMN IF NOT EXISTS temp_path text;
ALTER TABLE imagenes ADD COLUMN IF NOT EXISTS secure_url text;

CREATE TABLE IF NOT EXISTS analisis (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    imagen_id uuid NOT NULL REFERENCES imagenes(id) ON DELETE CASCADE,
    modelo text NOT NULL,
    person_count integer NOT NULL DEFAULT 0,
    detections jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS alertas (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    obra_id uuid REFERENCES obras(id) ON DELETE SET NULL,
    analisis_id uuid REFERENCES analisis(id) ON DELETE CASCADE,
    imagen_id uuid REFERENCES imagenes(id) ON DELETE CASCADE,
    tipo text NOT NULL,
    descripcion text NOT NULL DEFAULT '',
    nivel text NOT NULL DEFAULT 'baja',
    resuelta boolean NOT NULL DEFAULT false,
    mensaje text,
    created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE alertas ADD COLUMN IF NOT EXISTS obra_id uuid REFERENCES obras(id) ON DELETE SET NULL;
ALTER TABLE alertas ADD COLUMN IF NOT EXISTS descripcion text NOT NULL DEFAULT '';
ALTER TABLE alertas ADD COLUMN IF NOT EXISTS nivel text NOT NULL DEFAULT 'baja';
ALTER TABLE alertas ADD COLUMN IF NOT EXISTS resuelta boolean NOT NULL DEFAULT false;
ALTER TABLE alertas ALTER COLUMN mensaje DROP NOT NULL;

CREATE TABLE IF NOT EXISTS logs (
    id bigserial PRIMARY KEY,
    nivel text NOT NULL,
    mensaje text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
"""


def _normalized_url(raw: str) -> str:
    """Strip the literal ``[]`` from Supabase's password placeholder and encode it."""
    scheme_end = raw.index("://") + 3
    at = raw.index("@", scheme_end)
    prefix, password, suffix = raw[:scheme_end], raw[scheme_end:at], raw[at:]
    if ":" not in password:
        return raw
    user, secret = password.split(":", 1)
    if secret.startswith("[") and secret.endswith("]"):
        secret = secret[1:-1]
    if "%" not in secret:  # already percent-encoded URLs are left alone
        secret = quote(secret, safe="")
    return f"{prefix}{user}:{secret}{suffix}"


def _with_port(url: str, port: int) -> str:
    parts = urlsplit(url)
    netloc = f"{parts.username}:{parts.password}@{parts.hostname}:{port}"
    return urlunsplit((parts.scheme, netloc, parts.path, "", ""))


def main() -> None:
    if not DB_URL:
        sys.exit(
            "Falta SUPABASE_DB_URL en .env "
            "(postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres)"
        )

    normalized = _normalized_url(DB_URL)
    # Some Supabase projects only expose the pooled port on this host.
    candidates = [normalized]
    if urlsplit(normalized).port == 5432:
        candidates.append(_with_port(normalized, 6543))

    for url in candidates:
        result = subprocess.run(
            ["psql", url, "-v", "ON_ERROR_STOP=1", "-q", "-f", "-"],
            input=SQL,
            text=True,
            capture_output=True,
        )
        if result.returncode == 0:
            print(
                "Tablas creadas/verificadas: "
                "usuarios, obras, imagenes, analisis, alertas, logs"
            )
            return
        if "refused" not in (result.stderr or "").lower() and "rehusada" not in (
            result.stderr or ""
        ).lower():
            sys.exit(result.stderr.strip() or "psql falló")

    sys.exit(result.stderr.strip() or "psql falló")


if __name__ == "__main__":
    main()
