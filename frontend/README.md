# Supervisor IA · Frontend

Panel SaaS de supervisión de obras construido con React, Vite, TypeScript y TailwindCSS.

## Arranque

```bash
npm install
cp .env.example .env   # ajusta VITE_API_URL si el backend no está en :8000
npm run dev
```

El backend debe estar corriendo en `http://localhost:8000` (ver `main.py` en la raíz).

## Scripts

| Script | Uso |
| --- | --- |
| `npm run dev` | Servidor de desarrollo |
| `npm run build` | Verificación de tipos + build de producción |
| `npm run preview` | Servir el build localmente |
| `npm run lint` | Linter del proyecto |

## Estructura

- `src/lib/api.ts`: instancia de Axios con el JWT en cada request y helpers por dominio.
- `src/lib/ws.ts`: construye la URL de `/ws/alertas` con el token.
- `src/hooks/useWebSocket.ts`: conexión, reconexión con backoff y alarmas recibidas.
- `src/context/`: Auth, Theme (oscuro por defecto) y WebSocket compartidos.
- `src/components/layout/`: `AppLayout`, `Sidebar` y `Header`.
- `src/components/ui/`: `Card`, `Button`, `Input`, `Select`, `Badge`, `Modal`, `Toast`.
- `src/pages/`: `Login`, `Dashboard`, `Obras`, `Alertas`.

El JWT se guarda en `localStorage` bajo `supervisor_ia_token`. La sesión se limpia automáticamente ante un `401`.
